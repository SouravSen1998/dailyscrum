import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER', 'root')}:{os.getenv('MYSQL_PASSWORD', 'password')}"
        f"@{os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DB', 'daily_scrum')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
    JIRA_EMAIL = os.getenv("JIRA_EMAIL")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
    JIRA_JQL = os.getenv("JIRA_JQL", "ORDER BY updated DESC")
    JIRA_CLIENT_NAME_FIELD_ID = os.getenv("JIRA_CLIENT_NAME_FIELD_ID", "customfield_11555")
    JIRA_L0_ASSIGNEE_FIELD_ID = os.getenv("JIRA_L0_ASSIGNEE_FIELD_ID", "customfield_11680")
    JIRA_TES_SUPERVISION_FIELD_ID = os.getenv(
        "JIRA_TES_SUPERVISION_FIELD_ID", "customfield_11672"
    )
    JIRA_PCMC_INCLUSION_DATE_FIELD_ID = os.getenv(
        "JIRA_PCMC_INCLUSION_DATE_FIELD_ID", "customfield_11590"
    )
    JIRA_IMPACT_MODULE_FIELD_ID = os.getenv(
        "JIRA_IMPACT_MODULE_FIELD_ID", "customfield_12860"
    )
