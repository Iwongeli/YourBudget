# YOUR PROJECT TITLE
#### Video Demo:  https://youtu.be/QJAKA5YQmok
#### Description:
Your Budget is an app that supports you in creating budgets for your projects. During my participation in students organisations many times we face problem of creating budget for our project. I hope that this application will help in better structuring the budget for projects.

App.py contains whole app written in python with flask. It contains all the nodes that app uses:
-Configure session to use filesystem
-Configure db to be yourwallet.db

helpers.py
-contains two funcions that are imported to app.py

templates
-contains all templates that routes referes to.
-most importantly layout.html that is a base for others html pages and import bootsrap and chart.js. contains basic layout that can be modified with jinja. It contains navbar layout.

static
-contains
    -styles.css that corrects navbar
    -favicon.ico that is an icon for web app

requrements.txt
-provide requirements for flask

flask_session
-stores session as a file (not in cookies).

yourwallet.db
    contains 3 tables

    -users- store:
                        username,
                        hash of password,
                        index that is unique for all users
    -operations- store:
                        user id (ref to users),
                        operation id,
                        all record data (9),
                            in it category as int (ref to categories),
                            operation type as 0/1 for expenses/income
    -categories- store:
                        user id (ref to users),
                        category as int,
                        category as text,
                        category value

   -for app.py-
   about routes:
   
        -register-
        GET render register.html
        POST takes provided username password and password confirmation then:
            -Checks if all data are provided at all.
            -Ensure username is not in use.
            -Ensure there are no special characters or spaces in username or password. It checks it with function from helpers.py
            -Ensure password and corfirmation are the same.

            -If all terms are fulfilled then it hash provided passowrd with werkzeug.security and add it with username to database in yourwallet.db users table.
            -Else it prompt error message that tell user what should be done.

    -login-
        GET render login.html
        POST takes provided username and password and search for it in users table in database.
            -Ensure username and password were submitted
            -Ensure username exists and password is correct with werkzeug.security
            -If all goes well remember which user has logged in and redirect to "/".

    -logout-
        Simply: Forget any user_id, and redirect to "/" but becouse you are no longer loged in it redirect automaticly to login route.

    /From here all routes require beeing log in it checks it with function from helpers.py/

    -/-
        GET render index.html
        POST it creates new record that minimally takes title, value, quantity, date, operation type and optionally user can provide notes and external link
            -It takes today date and automaticly insert it into date place as well as quantity def value is 1.
            -Get list of categories that this user created from db and list them.
            -chcecks if value and quantity are numbers it allso can change , for . in value between numbers.
            -calculate total by formula value * quantity and add to record as well
            -return succes if all provided correctly else it prompt error message that tell user what should be done.

    -statistics-
        GET render statistics.html
        /this html uses charts.js to create charts and data from database provided with jinja2./
            -creates charts with charts.js: 2 pie chats that analyze expenses and incomes by taking all records in given time, by default from account, shows balance and acumulative chart in given time that helps better understand your budget.
        POST filter data for the charts
            -filter with dates if provided if not take long period of time (from 2000 to 2099) to include with high probability all records

    -categories-
        GET render categories.html
        POST Simply add category to db categories table that lets create record on that base
            -categories/del/id
                POST every category have delete button that create url to this route in effect given category is deleted from db as well as all its records.
                    -render back categories.html

    -history-
        GET render history.html
            -Gives you all records that were provided from database operations table with most impotant informations
        POST
            -Let you filter records with operation category and date
            -if no date provided take long period of time (from 2000 to 2099) to include with high probability all records

            -Gives you two options for each row to delete from db and explore further creates url
                -history_explore-
                    POST render history_explore.html
                        -Show all informations about given record
                -history_delete-
                    POST
                        -delete from database operations as well as decrese value of category
