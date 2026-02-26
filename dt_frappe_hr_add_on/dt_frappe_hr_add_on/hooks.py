app_name = "dt_frappe_hr_add_on"
app_title = "DT-Frappe HR Add-on"
app_publisher = "Digitalis Technologies Pvt. Ltd."
app_description = "additional customizations in Frappe HR"
app_email = "contact@digitalistech.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/dt_frappe_hr_add_on/css/dt_frappe_hr_add_on.css"
# app_include_js = "/assets/dt_frappe_hr_add_on/js/dt_frappe_hr_add_on.js"

# include js, css files in header of web template
# web_include_css = "/assets/dt_frappe_hr_add_on/css/dt_frappe_hr_add_on.css"
# web_include_js = "/assets/dt_frappe_hr_add_on/js/dt_frappe_hr_add_on.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dt_frappe_hr_add_on/public/scss/website"

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

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "dt_frappe_hr_add_on/public/icons.svg"

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
# 	"methods": "dt_frappe_hr_add_on.utils.jinja_methods",
# 	"filters": "dt_frappe_hr_add_on.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "dt_frappe_hr_add_on.install.before_install"
# after_install = "dt_frappe_hr_add_on.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "dt_frappe_hr_add_on.uninstall.before_uninstall"
# after_uninstall = "dt_frappe_hr_add_on.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "dt_frappe_hr_add_on.utils.before_app_install"
# after_app_install = "dt_frappe_hr_add_on.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "dt_frappe_hr_add_on.utils.before_app_uninstall"
# after_app_uninstall = "dt_frappe_hr_add_on.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dt_frappe_hr_add_on.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dt_frappe_hr_add_on.tasks.all"
# 	],
# 	"daily": [
# 		"dt_frappe_hr_add_on.tasks.daily"
# 	],
# 	"hourly": [
# 		"dt_frappe_hr_add_on.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dt_frappe_hr_add_on.tasks.weekly"
# 	],
# 	"monthly": [
# 		"dt_frappe_hr_add_on.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "dt_frappe_hr_add_on.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dt_frappe_hr_add_on.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dt_frappe_hr_add_on.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["dt_frappe_hr_add_on.utils.before_request"]
# after_request = ["dt_frappe_hr_add_on.utils.after_request"]

# Job Events
# ----------
# before_job = ["dt_frappe_hr_add_on.utils.before_job"]
# after_job = ["dt_frappe_hr_add_on.utils.after_job"]

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
# 	"dt_frappe_hr_add_on.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

doc_events = {
    "Salary Slip": {
		"before_save" : "dt_frappe_hr_add_on.dt_frappe_hr_add_on.methods.salary_component.add_component",
        # "before_validate" : "dt_frappe_hr_add_on.dt_frappe_hr_add_on.customized_methods.additional_components.additional_components"
	},
    "Salary Structure Assignment": {
        # "before_save" : "dt_frappe_hr_customization.customized_methods.salary_component.additional_validation_before_save",
		"on_submit" : "dt_frappe_hr_add_on.dt_frappe_hr_add_on.methods.salary_component.add_salary_component",
	},
    # "Salary Structure Assignment": {
	# 	"on_submit" : "dt_frappe_hr_customization.customized_methods.salary_component.another_method",
	# },
    "Journal Entry": {
        'before_save' : "dt_frappe_hr_add_on.controllers.jv.add_contributions_to_jv"
    }
}

fixtures = [
	{
        "dt": "Custom Field", 
        "filters": [["module", "in", ["DT-Frappe HR Add-on"]]]
    }
]

doctype_js = {"Salary Structure" : "controllers/salary_structure.js"}