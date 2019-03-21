# Copyright (c) 2019, Si Hay Sistema and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):
	# Assigning the list of columns and the list of data to the variables that will be returned for rendering the report
	# columns, data = [], []  # you can also assign them separately.
	if not filters: filters = {}
	salary_slips = get_salary_slips(filters)
	columns, earning_types, ded_types = get_columns(salary_slips)
	ss_earning_map = get_ss_earning_map(salary_slips)
	ss_ded_map = get_ss_ded_map(salary_slips)
	employee_singles = {}

	# en-US: We create an empty list, to which we will add the values of each row.
	# en-US:  The list contains within it a list of fields.  Each list of fields is a row.
	data = []
	for ss in salary_slips:
		"""row = [ss.start_date, ss.end_date, ss.name, ss.employee, ss.employee_name, ss.branch, ss.department, ss.designation,
			ss.company, ss.leave_withut_pay, ss.payment_days]"""
		row = [ss.start_date, ss.end_date, ss.name, ss.employee, ss.employee_name, ss.branch, ss.department, ss.designation,
			ss.company, ss.leave_without_pay, ss.payment_days, ss.total_working_days]

		if not ss.branch == None:columns[3] = columns[3].replace('-1','120')
		if not ss.department  == None: columns[4] = columns[4].replace('-1','120')
		if not ss.designation  == None: columns[5] = columns[5].replace('-1','120')
		if not ss.leave_without_pay  == None: columns[9] = columns[9].replace('-1','130')
			

		for e in earning_types:
			row.append(ss_earning_map.get(ss.name, {}).get(e))

		row += [ss.gross_pay]

		for d in ded_types:
			row.append(ss_ded_map.get(ss.name, {}).get(d))

		row += [ss.total_deduction, ss.net_pay]
		# Using the append method to add the row to the data list.
		data.append(row)

	return columns, data, employee_singles

def get_columns(salary_slips):
	"""
	columns = [
		_("Salary Slip ID") + ":Link/Salary Slip:150",_("Employee") + ":Link/Employee:120", _("Employee Name") + "::140", _("Branch") + ":Link/Branch:120",
		_("Department") + ":Link/Department:120", _("Designation") + ":Link/Designation:120",
		_("Company") + ":Link/Company:120", _("Start Date") + "::80", _("End Date") + "::80", _("Leave Without Pay") + ":Float:130",
		_("Payment Days") + ":Float:120"
	]
	"""
	columns = [
		_("Start Date") + "::80", _("End Date") + "::80", _("Salary Slip ID") + ":Link/Salary Slip:150",_("Employee") + ":Link/Employee:90", _("Employee Name") + "::110", _("Branch") + ":Link/Branch:-1",
		_("Department") + ":Link/Department:-1", _("Designation") + ":Link/Designation:-1",
		_("Company") + ":Link/Company:80", _("Leave Without Pay") + ":Float:-1",
		_("Payment Days") + ":Float:80"
	]	

	salary_components = {_("Earning"): [], _("Deduction"): []}

	for component in frappe.db.sql("""select distinct sd.salary_component, sc.type
		from `tabSalary Detail` sd, `tabSalary Component` sc
		where sc.name=sd.salary_component and sd.amount != 0 and sd.parent in (%s)""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1):
		salary_components[_(component.type)].append(component.salary_component)

	columns = columns + [(e + ":Currency:120") for e in salary_components[_("Earning")]] + \
		[_("Gross Pay") + ":Currency:120"] + [(d + ":Currency:120") for d in salary_components[_("Deduction")]] + \
		[_("Total Deduction") + ":Currency:120", _("Net Pay") + ":Currency:120"]

	return columns, salary_components[_("Earning")], salary_components[_("Deduction")]

# en-US: Gets salary slips, restricted by the date range chosen. It executes the query, with the given conditions.
def get_salary_slips(filters):
	filters.update({"from_date": filters.get("date_range")[0], "to_date":filters.get("date_range")[1]})
	conditions, filters = get_conditions(filters)
	salary_slips = frappe.db.sql("""select * from `tabSalary Slip` where docstatus = 1 %s
		order by employee""" % conditions, filters, as_dict=1)

	if not salary_slips:
		frappe.throw(_("No salary slip found between {0} and {1}").format(filters.get("from_date"), filters.get("to_date")))
	return salary_slips

def get_conditions(filters):
	conditions = ""
	if filters.get("date_range"): conditions += " and start_date >= %(from_date)s"
	if filters.get("date_range"): conditions += " and end_date <= %(to_date)s"
	if filters.get("company"): conditions += " and company = %(company)s"
	if filters.get("employee"): conditions += " and employee = %(employee)s"

	return conditions, filters

def get_ss_earning_map(salary_slips):
	ss_earnings = frappe.db.sql("""select parent, salary_component, amount
		from `tabSalary Detail` where parent in (%s)""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1)

	ss_earning_map = {}
	for d in ss_earnings:
		ss_earning_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, [])
		ss_earning_map[d.parent][d.salary_component] = flt(d.amount)

	return ss_earning_map

def get_ss_ded_map(salary_slips):
	ss_deductions = frappe.db.sql("""select parent, salary_component, amount
		from `tabSalary Detail` where parent in (%s)""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1)

	ss_ded_map = {}
	for d in ss_deductions:
		ss_ded_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, [])
		ss_ded_map[d.parent][d.salary_component] = flt(d.amount)

	return ss_ded_map
