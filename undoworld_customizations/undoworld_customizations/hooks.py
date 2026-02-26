app_name = "undoworld_customizations"
app_title = "Undoworld Customizations"
app_publisher = "Frappe Customizations"
app_description = "Undoworld Customizations"
app_email = "test@test.in"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/undoworld_customizations/css/undoworld_customizations.css"
# app_include_js = "/assets/undoworld_customizations/js/undoworld_customizations.js"

# include js, css files in header of web template
# web_include_css = "/assets/undoworld_customizations/css/undoworld_customizations.css"
# web_include_js = "/assets/undoworld_customizations/js/undoworld_customizations.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "undoworld_customizations/public/scss/website"

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

after_migrate = "undoworld_customizations.custom_field.setup_custom_fields"
# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "undoworld_customizations.utils.jinja_methods",
# 	"filters": "undoworld_customizations.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "undoworld_customizations.install.before_install"
# after_install = "undoworld_customizations.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "undoworld_customizations.uninstall.before_uninstall"
# after_uninstall = "undoworld_customizations.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "undoworld_customizations.utils.before_app_install"
# after_app_install = "undoworld_customizations.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "undoworld_customizations.utils.before_app_uninstall"
# after_app_uninstall = "undoworld_customizations.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "undoworld_customizations.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Order": {
		"before_insert": "undoworld_customizations.apis.sales_order_naming.before_insert",
		"on_update": "undoworld_customizations.apis.sales_order_update.on_update",
		"on_update_after_submit": "undoworld_customizations.apis.sales_order_update.on_update", 
	},
    "Stock Entry": {
        "on_submit": "undoworld_customizations.apis.stock_entry.on_submit"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"undoworld_customizations.tasks.all"
# 	],
# 	"daily": [
# 		"undoworld_customizations.tasks.daily"
# 	],
# 	"hourly": [
# 		"undoworld_customizations.tasks.hourly"
# 	],
# 	"weekly": [
# 		"undoworld_customizations.tasks.weekly"
# 	],
# 	"monthly": [
# 		"undoworld_customizations.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "undoworld_customizations.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "undoworld_customizations.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "undoworld_customizations.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["undoworld_customizations.utils.before_request"]
# after_request = ["undoworld_customizations.utils.after_request"]

# Job Events
# ----------
# before_job = ["undoworld_customizations.utils.before_job"]
# after_job = ["undoworld_customizations.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"undoworld_customizations.auth.validate"
# ]
