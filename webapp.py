#-----------------------------------------------------------------
# Carter Shean
# Application Development II
#-----------------------------------------------------------------

#get necessary modules
import bottle
from datetime import datetime
from mysql.connector import connect

#create connector
con = connect(user='root', password='passw0rd', database='wsoapp')
cursor = con.cursor()

#turn on autocommit
con.autocommit = True

#generate the template service table row in HTML
def getTemplateServices():

	#execute a cursor statement that gets all previous dates and orders them 
	cursor.execute("""
    	SELECT Svc_DateTime
    	FROM Service
    	ORDER BY Svc_DateTime
    	""")
	rowId = 0
	rows = ''

	#for each previous 
	for datetime in cursor.fetchall():
		row = """<option value="{0}">{1}</option>""".format( datetime[0], datetime[0])
		rowId += 1
		rows += row
	return """<tr> 
		<td class="inputlabel"> Template Date/Time:</td>
		<td> <select name="templateDate" class="inputDropDown"> {0} </select></td>
		</tr>""".format(rows)

#function that gets all previous songleaders and returns a table row containing them in a drop down box
def getSongLeader():

	#Get previous song leaders
	cursor.execute("""
		SELECT DISTINCT CONCAT(First_Name,' ',Last_Name)
		FROM Person
		INNER JOIN Service ON Service.Songleader_ID = Person.Person_ID
		""")

	rowId = 0
	rows = ''

	#loop over each of the songleaders, creating the options for the dropdown box
	for songleader in cursor.fetchall():
		row = """<option value="{0}">{1}</option>""".format(songleader[0], songleader[0])
		rowId += 1
		rows += row

	return """<tr> 
			<td class="inputlabel"> Songleader:</td>
			<td> <select name="songLeader"  class="inputDropDown"> {0} </select></td>
			</tr>""".format(rows)

#function that returns a table row in HTML containing the current date using Python's datetime.now() method
def getCurrentTime():
	return """<tr>
			 <td class="inputlabel">Date/Time(Enter YYYY-MM-DD HH:MM:SS.SS):</td>
			 <td><input type="text" id="theDate" value="{0}"class="inputBox" name="theDate"></td>
			 </tr>""".format(datetime.now())

#function that handles a request to the webpage 
@bottle.route('/')
def showPage():

	#open both the html and css for the webpage, read them in and display the template services and songleaders
    with open('index.html','r') as f:
        with open('./css/style.css') as g:
	        mainpage = f.read()
	        style = g.read()
	        templateServices = getTemplateServices()
	        songLeader = getSongLeader()
	        #return formatted page
	        return mainpage.format(style,"", getCurrentTime(), templateServices, songLeader)


#function that checks whether or not there is already a service at the current time
def checkCurrent(templateDate):
	templateDate = datetime.strptime(templateDate.split(".")[0], "%Y-%m-%d %H:%M:%S")
	cursor.execute("""
		SELECT SVC_DateTime From Service where %s = SVC_DateTime
	""", (templateDate,))

	#if there are no records with that date, return false
	if (len(cursor.fetchall()) == 0):
		return False
	#otherwise, return true
	else:
		return True

#function that inserts both the service and service event records for the new service, using the user supplied parameters from the HTML form
def insertService(serviceDate, templateDate, title, theme, songLeader):

	#convert the dates to a usable format
    serviceDate = datetime.strptime(serviceDate.split(".")[0], "%Y-%m-%d %H:%M:%S")
    templateDate = datetime.strptime(templateDate.split(".")[0], "%Y-%m-%d %H:%M:%S")

    #get the ID of the songleader selected 
    firstName, lastName = songLeader.split(' ')
    songLeader = (firstName, lastName)
    getLeaderID = """ SELECT Person_ID FROM Person WHERE Person.First_Name = %s AND Person.Last_Name = %s """
    cursor.execute(getLeaderID, songLeader)

    #If the user didn't supply either title, theme or songleader, set their values equal to Null(None)
    if (title == ''):
	    title = None
    if(theme == ''):
	    theme = None
    if(songLeader == ''):
	    songleader = None
	    print(cursor.fetchall())
    else:
        songleader =  cursor.fetchall()[0][0]

    #get the last serviceID and increment it by one to get the new serviceID
    getServiceID = """ SELECT Service_ID FROM Service ORDER BY Service_ID """
    cursor.execute(getServiceID)
    temp = cursor.fetchall()
    serviceID = int(temp[len(temp) - 1][0]) + 1

    #get the last serviceEventID and incerement it by one to get the new starting serviceEventID
    getServiceEventID = """ SELECT Event_ID FROM ServiceEvent ORDER BY Event_ID """
    cursor.execute(getServiceEventID)
    temp = cursor.fetchall()
    serviceEventID = int(temp[len(temp) - 1][0]) + 1


    #Insert the new service
    thingsToInsert = (serviceID, serviceDate,title,theme,songleader)
    insertStatement = """INSERT INTO Service(Service_ID, Svc_DateTime, Theme, Title, Notes, Organist_Conf, Songleader_Conf, Pianist_Conf, Organist_ID, Songleader_ID, Pianist_ID)
     					VALUES(%s, %s, %s, %s, NULL, 'N', 'N', 'N', NULL, NULL, %s)"""
    cursor.execute(insertStatement, thingsToInsert)

    #Get the template service ID based on the date supplied by the user from the dropdown
    templateDateTuple = (templateDate,)
    specificService = """SELECT *  
    					FROM Service 
    					WHERE Svc_DateTime = %s"""

    cursor.execute(specificService, templateDateTuple)
    templateServiceID =  (cursor.fetchall()[0][0],)


    #loop over the service events in the template service and insert new records
    ServiceEventSelect = """SELECT * 
    						FROM ServiceEvent
    					    INNER JOIN Service 
    					    ON ServiceEvent.Service_ID = Service.Service_ID
    					    WHERE ServiceEvent.Service_ID = %s"""

    cursor.execute(ServiceEventSelect, templateServiceID)
    newServiceEventInsert = """INSERT INTO ServiceEvent(Event_ID, Service_ID, Seq_Num, EventType_ID, Notes, Confirmed, Person_ID, Ensemble_ID, Song_ID)
     							VALUES(%s, %s, %s, %s, NULL, 'N', NULL, NULL, NULL)"""
    for line in cursor.fetchall():
    	cursor.execute(newServiceEventInsert, (serviceEventID, serviceID, line[2], line[3]))
    	serviceEventID += 1

#function that handles the creation of a new Service when the create button is pressed
@bottle.route('/create')
def createService():
	#open both the html and css and read their contents
    with open('index.html','r') as f:
        with open('./css/style.css') as g:
            mainpage = f.read()
            style = g.read()
            templateServices = getTemplateServices()
            songLeader = getSongLeader()
           
           #if there is already a service at that date or they didn't supply a date, do nothing and return an error message
            if  (bottle.request.params['theDate'] == '' or bottle.request.params['theDate']  checkCurrent(bottle.request.params['theDate']) == True):
                return mainpage.format(style,'<p style="color: red; text-align: center;">Unable to insert record!</p>', getCurrentTime(),templateServices, songLeader)
            #otherwise, proceed inserting a new service
            else:
            	insertService(bottle.request.params['theDate'],bottle.request.params['templateDate'], bottle.request.params['title'], bottle.request.params['theme'], bottle.request.params['songLeader'])
            	return mainpage.format(style,'<p style="color: green; text-align: center;">Service created!</p>',getCurrentTime(),templateServices, songLeader)
				

# Launch the BottlePy dev server
if __name__ == "__main__":
    bottle.run(host='localhost', debug=True)

