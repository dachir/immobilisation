from . import __version__ as app_version

app_name = "immobilisation"
app_title = "Immobilisation"
app_publisher = "Richard Amouzou"
app_description = "Gestion des Immobilisations avec la particularité du congo"
app_email = "dodziamouzou@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/immobilisation/css/immobilisation.css"
# app_include_js = "/assets/immobilisation/js/immobilisation.js"

# include js, css files in header of web template
# web_include_css = "/assets/immobilisation/css/immobilisation.css"
# web_include_js = "/assets/immobilisation/js/immobilisation.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "immobilisation/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "immobilisation.utils.jinja_methods",
#	"filters": "immobilisation.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "immobilisation.install.before_install"
# after_install = "immobilisation.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "immobilisation.uninstall.before_uninstall"
# after_uninstall = "immobilisation.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "immobilisation.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
    "Asset": "immobilisation.overrides.asset.CustomAsset"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"immobilisation.tasks.all"
#	],
#	"daily": [
#		"immobilisation.tasks.daily"
#	],
#	"hourly": [
#		"immobilisation.tasks.hourly"
#	],
#	"weekly": [
#		"immobilisation.tasks.weekly"
#	],
#	"monthly": [
#		"immobilisation.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "immobilisation.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "immobilisation.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "immobilisation.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["immobilisation.utils.before_request"]
# after_request = ["immobilisation.utils.after_request"]

# Job Events
# ----------
# before_job = ["immobilisation.utils.before_job"]
# after_job = ["immobilisation.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"immobilisation.auth.validate"
# ]

fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "Immobilisation"]]},
    {"dt": "Client Script", "filters": [["enabled", "=", 1],["module", "=", "Immobilisation"]]},
    {"dt": "Server Script", "filters": [["disabled", "=", 0],["module", "=", "Immobilisation"]]},
    {"dt": "Report", "filters": [["disabled", "=", 0],["module", "=", "Immobilisation"]]},
]

