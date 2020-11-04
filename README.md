# slack-semaphore-integration

Semaphore integration with slack for triggering pipelines 

To run this code,

1. Clone the repo
2. Run `pip3 install -r requirements.txt`
3. Update `slack.settings.py`


        SLACK_CLIENT_ID = "YOUR CLIENT ID"
        SLACK_CLIENT_SECRET = "YOUR CLIENT SECRET"

4. Run the following commands


        pytho3 manage.py makemigrations
        python3 manage.py migrate
        python3 manage.py runserver
        python3 manage.py listener
