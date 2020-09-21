import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import os
import random
import csv
import uuid
import math
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import datetime
class Scraper:

    def __init__(self):

        self.driver = None
        self.output = None
        self.hashtag_posts = []
        self.user_posts = []
        self.generated_uuid = uuid.uuid4()

        # Constants
        self.userid_instagram_url = "https://www.instagram.com/{}"
        self.hashtag_instagram_url = "https://www.instagram.com/explore/tags/{}/"
        self.post_base_url = "https://www.instagram.com/p/"

        # Constants - Credentials
        self.log_in_url = "https://www.instagram.com/"
        self.instagram_username = "sylisdavern7"
        self.instagram_password = "password#@!"

        with open("user_agents.txt", "r") as f:
            user_agents = f.readlines()
            self.user_agents = [i.strip().strip("\n") for i in user_agents]

    def write_csv(self,file,row):
        with open(file, "a", newline='', encoding="utf-8") as f:
            csv_writer = csv.writer(f,delimiter=',',quotechar='"')
            csv_writer.writerow(row)

    def get_driver(self):

        user_agent = random.choice(self.user_agents)

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("user-agent="+str(user_agent))
        # chrome_options.add_argument("headless")
        chrome_options.add_argument("no-sandbox")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("disable-logging")
        # chrome_options.add_argument("log-level=3")
        
        self.driver = webdriver.Chrome(options=chrome_options,executable_path="c_driver/chromedriver.exe")

    def setup(self):
        self.get_driver()
        self.log_in()
        self.output = os.path.join(os.getcwd(), "{}.csv".format(self.generated_uuid))
        self.write_csv(self.output,["ID","Data Type","Username","Number of followers", "Number of following", "Description", "Number of Likes","URL"])

    def get_scroll_num(self,n):
        if n <= 400:
            x = math.ceil(n/12)
        else:
            x = math.ceil(400/12)
            
        # print("{} posts".format(n))
        print("Scrolling {} times".format(x))
        return x

    def scroll_down(self, scrape_type, num_posts):

        num_scrolldowns = self.get_scroll_num(num_posts)

        if scrape_type == 'hashtag':
            for i in range(num_scrolldowns):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                self.hashtag_posts.extend(post.get_attribute("href") for post in self.driver.find_elements_by_tag_name("a") if "https://www.instagram.com/p/" in post.get_attribute("href") and post.get_attribute("href") not in self.hashtag_posts)
            print("{} hashtag posts fetched".format(len(self.hashtag_posts)))

        if scrape_type == 'user':
            for i in range(num_scrolldowns):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                self.user_posts.extend(post.get_attribute("href") for post in self.driver.find_elements_by_tag_name("a") if "https://www.instagram.com/p/" in post.get_attribute("href") and post.get_attribute("href") not in self.user_posts)
            print("{} user posts fetched".format(len(self.user_posts)))

    def download_image(self,image,id):
        print("Downloading image {}".format(image))

        try:
            response = requests.get(image, timeout=15)
            img_path = "images/"+str(id) + "_{} (".format(self.generated_uuid)+").jpg"
            now = datetime.datetime.now()
            #Writing image to file
            file = open(img_path, "wb")
            file.write(response.content)
            file.close()
            print("Image successfully downloaded...")
        except:
            print("couldn't fetch image")

    def scrape_userid(self,userid):

        username = userid
        url = self.userid_instagram_url.format(username)
        self.driver.get(url)
        self.user_posts = [post.get_attribute("href") for post in self.driver.find_elements_by_tag_name("a") if "https://www.instagram.com/p/" in post.get_attribute("href")]

        num_posts = self.fetch_numposts()
        self.scroll_down('user',num_posts)

        time.sleep(3)
        print("Post links fetched completely")
        print("{} Posts fetched".format(len(self.user_posts)))

        num_followers = self.driver.find_elements_by_class_name('g47SY')[1].text
        num_following = self.driver.find_elements_by_class_name('g47SY')[2].text

        print("Iterating trough posts...")
        id = 0
        for post in self.user_posts:
            id+=1
            data_type = ""
            description = ""
            post_url = post

            self.driver.get(post_url)
            print("Scraping: {}".format(post_url))

            #fetching description
            try:
                desc = self.driver.find_element_by_xpath("//div[@class='C4VMK']/span")
            except Exception as e:
                # Description is empty
                print("Description is empty")
            else:
                description = desc.text

            #VIDEO CHECK
            video_button = self.driver.find_elements_by_class_name('tWeCl')
            if len(video_button) != 0:
                print("VIDEO")
                data_type = "Video"
                num_likes = ""
                row = [id,data_type,username,num_followers,num_following,description,num_likes,post_url]
                self.write_csv(self.output,row)
                continue

            num_likes = self.driver.find_element_by_xpath("//button[@class='sqdOP yWX7d     _8A5w5    ']").text.rstrip(" likes")

            # SLIDESHOW CHECK
            slideshow = self.driver.find_elements_by_xpath("//div[@class='    coreSpriteRightChevron  ']")
            if len(slideshow) != 0:
                print("SLIDESHOW")
                data_type = "Slideshow"
                row = [id,data_type,username,num_followers,num_following,description,num_likes,post_url]
                self.write_csv(self.output,row)
                continue


            #IMAGE
            data_type = "Image"
            row = [id,data_type,username,num_followers,num_following,description,num_likes,post_url]
            self.write_csv(self.output,row)
            
            image = self.driver.find_element_by_class_name('FFVAD').get_attribute('srcset').split(' ')[0]
            self.download_image(image,id)

        self.driver.quit()
        print('done')
        exit()

    def log_in(self):
        try:
            print("Logging in")
            self.driver.get(self.log_in_url)
            self.driver.implicitly_wait(5)

            username_field = self.driver.find_element_by_name('username')
            password_field = self.driver.find_element_by_name('password')
            log_in_button = self.driver.find_elements_by_xpath("//div[text()='Log In']")[0]

            username_field.send_keys(self.instagram_username)  
            password_field.send_keys(self.instagram_password)

            log_in_button.click()

            self.driver.implicitly_wait(5)

            if self.driver.find_elements_by_css_selector("[aria-label=Home]")[0].get_attribute('fill'):
                print('Logged in')
        except Exception as e:
            print("Exception")
            self.driver.quit()
            exit()

    def fetch_numposts(self):
        element = self.driver.find_element_by_class_name('-nal3').text.rstrip(" posts")
        print(element+" num of posts in this page")
        return int(element.replace(',', ''))

    def scrape_hashtag_posts(self,hashtag):
        self.hashtag_posts = []
        self.driver.get(self.hashtag_instagram_url.format(hashtag))
        self.driver.implicitly_wait(5)
        self.hashtag_posts = [post.get_attribute("href") for post in self.driver.find_elements_by_tag_name("a") if "https://www.instagram.com/p/" in post.get_attribute("href")]
        self.hashtag_num_posts = self.fetch_numposts()
        self.scroll_down('hashtag',self.hashtag_num_posts)
        self.process_scraped_posts(self.hashtag_posts)

    def process_scraped_posts(self, posts):

        num_followers = 'unknown'
        num_following = 'unknown'
        username = 'unknown'

        # Number of followers and following     
        try:
            num_followers = self.driver.find_elements_by_class_name('g47SY')[1].text
            num_following = self.driver.find_elements_by_class_name('g47SY')[2].text
        except:
            print('Number of followers and following unavailable')

        id = 0
        for post in posts:
            id += 1
            data_type = ""
            description = ""
            post_url = post

            print("Scraping: {}".format(post_url))

            self.driver.get(post_url)

            # Username
            try:
                username = self.driver.find_element_by_xpath("//div[@class='e1e1d']/span[@class='Jv7Aj  MqpiF  ' and 1]/a[@class='sqdOP yWX7d     _8A5w5   ZIAjV ' and 1]").text
            except:
                username = 'unavailable'

            # Likes
            try:
                num_likes = self.driver.find_element_by_xpath("//button[@class='sqdOP yWX7d     _8A5w5    ']").text.rstrip(" likes")
            except:
                num_likes = 'unavailable'

            # Description
            try:
                desc = self.driver.find_element_by_xpath("//div[@class='C4VMK']/span")
            except Exception as e:
                print("Description is empty")
            else:
                description = desc.text

            # Video
            video_button = self.driver.find_elements_by_class_name('tWeCl')
            if len(video_button) != 0:
                data_type = "Video"
                num_likes = ""
                row = [id,data_type,username,num_followers,num_following,description,num_likes,post_url]
                self.write_csv(self.output,row)
                continue

            # Slideshow
            slideshow = self.driver.find_elements_by_xpath("//div[@class='    coreSpriteRightChevron  ']")
            if len(slideshow) != 0:
                data_type = "Slideshow"
                row = [id,data_type,username,num_followers,num_following,description,num_likes,post_url]
                self.write_csv(self.output,row)
                continue

            # Image
            data_type = "Image"
            row = [id,data_type,username,num_followers,num_following,description,num_likes,post_url]
            self.write_csv(self.output,row)
            

            image = self.driver.find_element_by_class_name('FFVAD').get_attribute('srcset').split(' ')[0]
            self.download_image(image, id)

if __name__=="__main__":
    s = Scraper()
    s.setup()
    decision = int(input("Insert 1 for scraping userID or enter 2 for scraping hashtag\n"))
    if decision == 1:
        userid = input("Enter the userid\n")
        s.scrape_userid(userid)
    elif decision == 2:
        hashtag = input("Enter the hashtag\n")
        s.scrape_hashtag_posts(hashtag)
    else:
        print("Invalid decision")

