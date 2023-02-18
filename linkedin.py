import time
import math
import random
import os
import utils
import constants
import config
import json

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from utils import prRed, prYellow, prGreen

from webdriver_manager.chrome import ChromeDriverManager


class Linkedin:
    def __init__(self, credentials):
        try:
            self.driver = webdriver.Chrome(ChromeDriverManager().install())
            self.driver.get(
                "https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
            prYellow("Trying to log in linkedin.")
        except Exception as e:
            prRed("Warning ChromeDriver" + str(e))
        try:
            self.driver.find_element(
                "id", "username").send_keys(credentials["email"])
            time.sleep(5)
            self.driver.find_element("id", "password").send_keys(
                credentials["password"])
            time.sleep(5)
            self.driver.find_element(
                "xpath", '//*[@id="organic-div"]/form/div[3]/button').click()
        except:
            prRed("Couldnt log in Linkedin.")

    def generateUrls(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        try:
            with open('data/urlData.txt', 'w', encoding="utf-8") as file:
                linkedinJobLinks = utils.LinkedinUrlGenerate().generateUrlLinks()
                for url in linkedinJobLinks:
                    file.write(url + "\n")
            prGreen(
                "Urls are created successfully, now the bot will visit those urls.")
        except:
            prRed("Couldnt generate url, make sure you have /data folder and modified config.py file for your preferances.")

    def linkJobApply(self):
        self.generateUrls()
        countApplied = 0
        countJobs = 0

        urlData = utils.getUrlDataFile()

        for url in urlData:
            self.driver.get(url)
            ignoredExceptions = (NoSuchElementException,
                                 StaleElementReferenceException)
            totalJobs = WebDriverWait(self.driver, 5, ignored_exceptions=ignoredExceptions).until(
                EC.presence_of_element_located((By.XPATH, '//small'))).text
            totalPages = utils.jobsToPages(totalJobs)

            urlWords = utils.urlToKeywords(url)
            csvName = [urlWords[0], urlWords[1]]  # [keyword, location]

            for page in range(totalPages):
                currentPageJobs = constants.jobsPerPage * page
                url = url + "&start=" + str(currentPageJobs)
                self.driver.get(url)
                time.sleep(random.uniform(1, constants.botSpeed))

                offersPerPage = WebDriverWait(self.driver, 5, ignored_exceptions=ignoredExceptions).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//li[@data-occludable-job-id]')))
                #offersPerPage = self.driver.find_elements(By.XPATH, '//li[@data-occludable-job-id]')

                offerIds = []

                for offer in offersPerPage:
                    # print(offer)
                    try:
                        jobId = offer.get_attribute("data-occludable-job-id")
                        offerId = int(jobId.split(":")[-1])
                        # if offerId not in alreadyApplied:
                        offerIds.append(offerId)
                    except StaleElementReferenceException as e:
                        print(offer)
                        print(e)

                for jobID in offerIds:
                    offerPage = 'https://www.linkedin.com/jobs/view/' + \
                        str(jobID)
                    self.driver.get(offerPage)
                    time.sleep(random.uniform(1, constants.botSpeed))

                    countJobs += 1
                    jobProperties = self.getJobProperties(countJobs)

                    if "blacklisted" in jobProperties:

                        # [properties, Applied, Reason, Link]
                        jobProperties.extend(
                            [False, "Blacklisted", jobID, str(offerPage)])
                        self.writeCsvData(csvName, jobProperties)
                    else:
                        button = self.easyApplyButton()

                        if button is not False:
                            try:
                                button.click()
                                time.sleep(random.uniform(
                                    1, constants.botSpeed))
                                countApplied += 1
                            except Exception as e:
                                print(e)
                                print(button)

                            try:
                                self.driver.find_element(
                                    By.CSS_SELECTOR, "button[aria-label='Submit application']").click()
                                time.sleep(random.uniform(
                                    1, constants.botSpeed))

                                # [properties, Applied, Reason, Link]
                                jobProperties.extend(
                                    [True, "Applied", jobID, str(offerPage)])
                                self.writeCsvData(
                                    csvName, jobProperties)

                            except:
                                try:
                                    self.driver.find_element(
                                        By.CSS_SELECTOR, "button[aria-label='Continue to next step']").click()
                                    time.sleep(random.uniform(
                                        1, constants.botSpeed))

                                    comPercentage = self.driver.find_element(
                                        By.XPATH, 'html/body/div[3]/div/div/div[2]/div/div/span').text
                                    percenNumber = int(
                                        comPercentage[0:comPercentage.index("%")])
                                    result = self.applyProcess(
                                        percenNumber, jobID, offerPage)

                                    # [properties, Applied, Reason, jobID, Link]
                                    jobProperties.extend(result)
                                    self.writeCsvData(
                                        csvName, jobProperties)

                                except Exception as e:

                                    # [properties, Applied, Reason, jobID, Link]
                                    jobProperties.extend(
                                        [False, "No Apply", jobID, str(offerPage)])
                                    self.writeCsvData(
                                        csvName, jobProperties)
                        else:

                            # [properties, Applied, Reason, Link]
                            jobProperties.extend(
                                [True, "Already applied", jobID, str(offerPage)])
                            self.writeCsvData(csvName, jobProperties)

            prYellow("Category: " + urlWords[0] + "," + urlWords[1] + " applied: " + str(countApplied) +
                     " jobs out of " + str(countJobs) + ".")

    def getJobProperties(self, count):
        jobTitle = ""
        jobCompany = ""
        jobLocation = ""
        jobWOrkPlace = ""
        jobPostedDate = ""
        jobApplications = ""

        try:
            jobTitle = self.driver.find_element(
                By.XPATH, "//h1[contains(@class, 'job-title')]").get_attribute("innerHTML").strip()
            res = [blItem for blItem in config.blackListTitles if (
                blItem.lower() in jobTitle.lower())]
            if (len(res) > 0):
                jobTitle += "(blaclisted title: " + ' '.join(res) + ")"
        except Exception as e:
            prYellow("Warning in getting jobTitle: " + str(e)[0:50])
            jobTitle = ""

        try:
            jobCompany = self.driver.find_element(
                By.XPATH, "//a[contains(@class, 'ember-view t-black t-normal')]").get_attribute("innerHTML").strip()
            res = [blItem for blItem in config.blacklistCompanies if (
                blItem.lower() in jobTitle.lower())]
            if (len(res) > 0):
                jobCompany += "(blaclisted company: " + ' '.join(res) + ")"
        except Exception as e:
            prYellow("Warning in getting jobCompany: " + str(e)[0:50])
            jobCompany = ""

        try:
            jobLocation = self.driver.find_element(
                By.XPATH, "//span[contains(@class, 'bullet')]").get_attribute("innerHTML").strip()
        except Exception as e:
            prYellow("Warning in getting jobLocation: " + str(e)[0:50])
            jobLocation = ""
        try:
            jobWOrkPlace = self.driver.find_element(
                By.XPATH, "//span[contains(@class, 'workplace-type')]").get_attribute("innerHTML").strip()
        except Exception as e:
            prYellow("Warning in getting jobWorkPlace: " + str(e)[0:50])
            jobWOrkPlace = ""
        try:
            jobPostedDate = self.driver.find_element(
                By.XPATH, "//span[contains(@class, 'posted-date')]").get_attribute("innerHTML").strip()
        except Exception as e:
            prYellow("Warning in getting jobPostedDate: " + str(e)[0:50])
            jobPostedDate = ""
        try:
            jobApplications = self.driver.find_element(
                By.XPATH, "//span[contains(@class, 'applicant-count')]").get_attribute("innerHTML").strip()
        except Exception as e:
            prYellow("Warning in getting jobApplications: " + str(e)[0:50])
            jobApplications = ""

        jobInfo = [count, jobTitle, jobCompany, jobLocation,
                   jobWOrkPlace, jobPostedDate, jobApplications]

        return jobInfo

    def easyApplyButton(self):
        try:
            time.sleep(3)
            ignoredExceptions = (NoSuchElementException,
                                 StaleElementReferenceException)
            button = WebDriverWait(self.driver, 5, ignored_exceptions=ignoredExceptions).until(
                EC.presence_of_element_located((By.XPATH, '//button[contains(@class, "jobs-apply-button")]')))

            EasyApplyButton = button
        except:
            EasyApplyButton = False

        return EasyApplyButton

    def applyProcess(self, percentage, jobID, offerPage):
        applyPages = math.floor(100 / percentage)
        try:
            resumeUpload = False

            for page in range(applyPages-1):
                pageTitle = ''
                try:
                    pageTitle = self.driver.find_element(
                        By.XPATH, "//h3[contains(@class, 't-16 t-bold')]").get_attribute("innerHTML").strip()
                except Exception as e:
                    prYellow('Warning in finding pageTitle: ' + str(e)[0:50])

                if pageTitle == 'Resume':
                    try:
                        self.driver.find_element(
                            By.CSS_SELECTOR, "button[aria-label='Choose Resume']").click()
                        time.sleep(random.uniform(1, constants.botSpeed))
                        resumeUpload = True
                    except Exception as e:
                        prYellow(
                            'Warning in finding Resume: ' + str(e)[0:50])

                elif pageTitle == 'Additional Questions' or pageTitle == 'Additional':
                    inputFields = self.driver.find_elements(
                        By.XPATH, "//input[contains(@type, 'text')]")

                    for inputField in inputFields:
                        fieldValue = inputField.get_attribute('value')

                        if len(fieldValue) == 0:
                            fieldClass = inputField.get_attribute('class')

                            if "text-input" in fieldClass:  # check if text field
                                fieldId = inputField.get_attribute('id')

                                if "numeric" in fieldId:  # id contains numeric
                                    inputField.send_keys('1')
                                    time.sleep(random.uniform(
                                        1, constants.botSpeed))

                                else:  # else field is text
                                    inputField.send_keys('Yes')
                                    time.sleep(random.uniform(
                                        1, constants.botSpeed))

                    dropFields = self.driver.find_elements(
                        By.XPATH, "//select[contains(@id, 'multipleChoice')]")

                    for dropField in dropFields:
                        fieldValue = dropField.get_attribute('value')

                        if fieldValue == 'Select an option':
                            select = Select(dropField)
                            select.select_by_index(1)
                            time.sleep(random.uniform(1, constants.botSpeed))

                    selectFields = self.driver.find_elements(
                        By.XPATH, "//input[contains(@type, 'radio')]")

                    for selectField in selectFields:
                        fieldValue = selectField.get_attribute('value')

                        if fieldValue == 'Yes':
                            selectField.click()
                            time.sleep(random.uniform(1, constants.botSpeed))

                try:  # Next button
                    self.driver.find_element(
                        By.CSS_SELECTOR, "button[aria-label='Continue to next step']").click()
                    time.sleep(random.uniform(1, constants.botSpeed))
                except:  # review button
                    self.driver.find_element(
                        By.CSS_SELECTOR, "button[aria-label='Review your application']").click()
                    time.sleep(random.uniform(1, constants.botSpeed))

            if config.followCompanies is False:
                self.driver.find_element(
                    By.CSS_SELECTOR, "label[for='follow-company-checkbox']").click()
                time.sleep(random.uniform(1, constants.botSpeed))

            self.driver.find_element(
                By.CSS_SELECTOR, "button[aria-label='Submit application']").click()
            time.sleep(random.uniform(1, constants.botSpeed))

            # [applied?, message, link]
            resultArray = [True, "Applied", jobID, str(offerPage)]
        except:
            resultArray = [False, "Info", jobID, str(offerPage)]
        return resultArray

    def writeCsvData(self, csvName: list, csvData: list):
        try:
            utils.writeCSV(csvName, csvData)
        except Exception as e:
            prRed("Error in writeCsvData: " + str(e))


if __name__ == '__main__':

    with open('credentials.json') as credentials_file:
        credentials = json.load(credentials_file)

    bot = Linkedin(credentials)
    #alreadyApplied = utils.alreadyApplied()
    bot.linkJobApply()
