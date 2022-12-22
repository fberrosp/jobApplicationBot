import time,math,random,os
import utils,constants,config
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from utils import prRed,prYellow,prGreen

from webdriver_manager.chrome import ChromeDriverManager

class Linkedin:
    def __init__(self, credentials):
        try:
            self.driver = webdriver.Chrome(ChromeDriverManager().install())
            self.driver.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
            prYellow("Trying to log in linkedin.")
        except Exception as e:
            prRed("Warning ChromeDriver"+ str(e))
        try:    
            self.driver.find_element("id","username").send_keys(credentials["email"])
            time.sleep(5)
            self.driver.find_element("id","password").send_keys(credentials["password"])
            time.sleep(5)
            self.driver.find_element("xpath",'//*[@id="organic-div"]/form/div[3]/button').click()
        except:
            prRed("Couldnt log in Linkedin.")

    
    def generateUrls(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        try: 
            with open('data/urlData.txt', 'w',encoding="utf-8" ) as file:
                linkedinJobLinks = utils.LinkedinUrlGenerate().generateUrlLinks()
                for url in linkedinJobLinks:
                    file.write(url+ "\n")
            prGreen("Urls are created successfully, now the bot will visit those urls.")
        except:
            prRed("Couldnt generate url, make sure you have /data folder and modified config.py file for your preferances.")

    def linkJobApply(self):
        self.generateUrls()
        countApplied = 0
        countJobs = 0

        urlData = utils.getUrlDataFile()

        for url in urlData:        
            self.driver.get(url)

            totalJobs = self.driver.find_element(By.XPATH,'//small').text 
            totalPages = utils.jobsToPages(totalJobs)

            urlWords =  utils.urlToKeywords(url)
            csvName = [urlWords[0], urlWords[1]] #[keyword, location]
            lineToWrite = "\n Category: " + urlWords[0] + ", Location: " +urlWords[1] + ", Applying " +str(totalJobs)+ " jobs."
            self.displayWriteResults(lineToWrite)

            for page in range(totalPages):
                currentPageJobs = constants.jobsPerPage * page
                url = url +"&start="+ str(currentPageJobs)
                self.driver.get(url)
                time.sleep(random.uniform(1, constants.botSpeed))

                offersPerPage = self.driver.find_elements(By.XPATH,'//li[@data-occludable-job-id]')

                offerIds = []
                for offer in offersPerPage:
                    offerId = offer.get_attribute("data-occludable-job-id")
                    offerIds.append(int(offerId.split(":")[-1]))

                for jobID in offerIds:
                    offerPage = 'https://www.linkedin.com/jobs/view/' + str(jobID)
                    self.driver.get(offerPage)
                    time.sleep(random.uniform(1, constants.botSpeed))

                    countJobs += 1
                    callJobProperties = self.getJobProperties(countJobs)
                    jobProperties = callJobProperties[0]

                    if "blacklisted" in jobProperties: 
                        lineToWrite = jobProperties + " | " + "* 🤬 Blacklisted Job, skipped!: " +str(offerPage)
                        self.displayWriteResults(lineToWrite)

                        callJobProperties[1].extend([False, "Blacklisted", str(offerPage)]) # [properties, Applied, Reason, Link]
                        self.writeCsvData(csvName, callJobProperties[1])
                    else :
                        button = self.easyApplyButton()

                        if button is not False:
                            button.click()
                            time.sleep(random.uniform(1, constants.botSpeed))
                            countApplied += 1
                            try:
                                self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']").click()
                                time.sleep(random.uniform(1, constants.botSpeed))

                                lineToWrite = jobProperties + " | " + "* 🥳 Just Applied to this job: "  +str(offerPage)
                                self.displayWriteResults(lineToWrite)

                                callJobProperties[1].extend([True, "Applied", str(offerPage)]) # [properties, Applied, Reason, Link]
                                self.writeCsvData(csvName, callJobProperties[1])

                            except:
                                try:
                                    self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Continue to next step']").click()
                                    time.sleep(random.uniform(1, constants.botSpeed))

                                    comPercentage = self.driver.find_element(By.XPATH,'html/body/div[3]/div/div/div[2]/div/div/span').text
                                    percenNumber = int(comPercentage[0:comPercentage.index("%")])
                                    result = self.applyProcess(percenNumber,offerPage)
                                    lineToWrite = jobProperties + " | " + result[0]
                                    self.displayWriteResults(lineToWrite)

                                    callJobProperties[1].extend(result[1]) # [properties, Applied, Reason, Link]
                                    self.writeCsvData(csvName, callJobProperties[1])
                                
                                except Exception as e: 
                                    lineToWrite = jobProperties + " | " + "* 🥵 Cannot apply to this Job! " +str(offerPage)
                                    self.displayWriteResults(lineToWrite)

                                    callJobProperties[1].extend([False, "No Apply", str(offerPage)]) # [properties, Applied, Reason, Link]
                                    self.writeCsvData(csvName, callJobProperties[1])
                        else:
                            lineToWrite = jobProperties + " | " + "* 🥳 Already applied! Job: " +str(offerPage)
                            self.displayWriteResults(lineToWrite)

                            callJobProperties[1].extend([True, "Already applied", str(offerPage)]) # [properties, Applied, Reason, Link]
                            self.writeCsvData(csvName, callJobProperties[1])


            prYellow("Category: " + urlWords[0] + "," +urlWords[1]+ " applied: " + str(countApplied) +
                  " jobs out of " + str(countJobs) + ".")
        
    def getJobProperties(self, count):
        textToWrite = ""
        jobTitle = ""
        jobCompany = ""
        jobLocation = ""
        jobWOrkPlace = ""
        jobPostedDate = ""
        jobApplications = ""

        try:
            jobTitle = self.driver.find_element(By.XPATH,"//h1[contains(@class, 'job-title')]").get_attribute("innerHTML").strip()
            res = [blItem for blItem in config.blackListTitles if(blItem.lower() in jobTitle.lower())]
            if (len(res)>0):
                jobTitle += "(blaclisted title: "+ ' '.join(res)+ ")"
        except Exception as e:
            prYellow("Warning in getting jobTitle: " +str(e)[0:50])
            jobTitle = ""

        try:
            jobCompany = self.driver.find_element(By.XPATH,"//a[contains(@class, 'ember-view t-black t-normal')]").get_attribute("innerHTML").strip()
            res = [blItem for blItem in config.blacklistCompanies if(blItem.lower() in jobTitle.lower())]
            if (len(res)>0):
                jobCompany += "(blaclisted company: "+ ' '.join(res)+ ")"
        except Exception as e:
            prYellow("Warning in getting jobCompany: " +str(e)[0:50])
            jobCompany = ""

        try:
            jobLocation = self.driver.find_element(By.XPATH,"//span[contains(@class, 'bullet')]").get_attribute("innerHTML").strip()
        except Exception as e:
            prYellow("Warning in getting jobLocation: " +str(e)[0:50])
            jobLocation = ""
        try:
            jobWOrkPlace = self.driver.find_element(By.XPATH,"//span[contains(@class, 'workplace-type')]").get_attribute("innerHTML").strip()
        except Exception as e:
            prYellow("Warning in getting jobWorkPlace: " +str(e)[0:50])
            jobWOrkPlace = ""
        try:
            jobPostedDate = self.driver.find_element(By.XPATH,"//span[contains(@class, 'posted-date')]").get_attribute("innerHTML").strip()
        except Exception as e:
            prYellow("Warning in getting jobPostedDate: " +str(e)[0:50])
            jobPostedDate = ""
        try:
            jobApplications= self.driver.find_element(By.XPATH,"//span[contains(@class, 'applicant-count')]").get_attribute("innerHTML").strip()
        except Exception as e:
            prYellow("Warning in getting jobApplications: " +str(e)[0:50])
            jobApplications = ""

        textToWrite = str(count)+ " | " +jobTitle+  " | " +jobCompany+  " | "  +jobLocation+ " | "  +jobWOrkPlace+ " | " +jobPostedDate+ " | " +jobApplications
        jobInfo = [count, jobTitle, jobCompany, jobLocation, jobWOrkPlace, jobPostedDate, jobApplications]
        return [textToWrite, jobInfo]

    def easyApplyButton(self):
        try:
            time.sleep(3)
            button = self.driver.find_element(By.XPATH,
                '//button[contains(@class, "jobs-apply-button")]')
            EasyApplyButton = button
        except: 
            EasyApplyButton = False

        return EasyApplyButton

    def applyProcess(self, percentage, offerPage):
        applyPages = math.floor(100 / percentage) 
        result = ""  
        try:
            resumeUpload = False
            for pages in range(applyPages-2):
                if not resumeUpload:
                    try:
                        #try finding resume button, if found, click it
                        self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Choose Resume']").click()
                        time.sleep(random.uniform(1, constants.botSpeed))
                        resumeUpload = True
                    except:
                        print('Choose Resume button not found yet')

                #check if information is needed before proceding
                #try catch for resume and select forms (input forms can be 1 by default)
                self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Continue to next step']").click()
                time.sleep(random.uniform(1, constants.botSpeed))

            self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Review your application']").click() 
            time.sleep(random.uniform(1, constants.botSpeed))

            if config.followCompanies is False:
                self.driver.find_element(By.CSS_SELECTOR,"label[for='follow-company-checkbox']").click() 
                time.sleep(random.uniform(1, constants.botSpeed))

            self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Submit application']").click()
            time.sleep(random.uniform(1, constants.botSpeed))

            result = "* 🥳 Just Applied to this job: " +str(offerPage)
            resultArray = [True, "Applied", str(offerPage)] #[applied?, message, link]
        except:
            result = "* 🥵 " +str(applyPages)+ " Pages, couldn't apply to this job! Extra info needed. Link: " +str(offerPage)
            resultArray = [False, "Info", str(offerPage)]
        return [result, resultArray]

    def displayWriteResults(self,lineToWrite: str):
        try:
            #print(lineToWrite)
            utils.writeResults(lineToWrite)
        except Exception as e:
            prRed("Error in DisplayWriteResults: " + str(e))

    def writeCsvData(self, csvName: list, csvData: list):
        #print(csvName)
        #print(csvData)
        try:
            utils.writeCSV(csvName, csvData)
        except Exception as e:
            prRed("Error in writeCsvData: " + str(e))

if __name__ == '__main__':

    with open('credentials.json') as credentials_file:
        credentials = json.load(credentials_file)

    bot = Linkedin(credentials)
    start = time.time()
    bot.linkJobApply()
    end = time.time()
    prYellow("---Took: " + str(round((time.time() - start)/60)) + " minute(s).")
