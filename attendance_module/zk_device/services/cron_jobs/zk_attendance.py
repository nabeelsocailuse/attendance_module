import frappe, time
from frappe import _
from frappe.model.document import Document
from frappe.utils import (date_diff, add_to_date, getdate, get_datetime)

# bench --site al-khidmat.com execute akf_hrms.zk_device.doctype.zk_tool.zk_tool.get_from_to
# def get_from_to():
# 	start_time = f"2025-08-07 14:00:00"
# 	end_time= f"2025-08-07 16:19:59"
# 	cur_datetime = get_datetime()
# 	print('------------------')
# 	print(cur_datetime)
# 	pre_datetime = add_to_date(cur_datetime, hours=-2)
# 	print(pre_datetime)

# bench --site erp.alkhidmat.org execute akf_hrms.services.cron_jobs.zk_attendance.del_attendance
def del_attendance():
	res = frappe.db.sql('''delete from `tabAttendance` 
				where docstatus=1 and status="Present" and attendance_date between '2025-07-21' and '2025-07-31'
				''', as_dict=1)	
	res = frappe.db.sql('''delete from `tabAttendance Log` 
			where docstatus=0 and ifnull(device_ip, '')!='' and attendance_date between '2025-07-21' and '2025-07-31'
			''', as_dict=1)
	# print(res)
# bench --site erp.alkhidmat.org execute akf_hrms.services.cron_jobs.zk_attendance.get_zk_attendance
def get_zk_attendance():
	
	import requests

	# Replace with the actual API URL
	# api_url = "http://zkteco.alkhidmat.tech/iclock/api/transactions/?"
	# terminal_ip_address = '192.168.19.106'
	terminal_ip_address = '10.0.7.201'
	emp_code = ""
	# start_time = f"2025-08-09 00:00:00"
	# end_time = f"2025-08-11 23:59:59"
	end_time = get_datetime()
	start_time = add_to_date(end_time, hours=-1, minutes=-30)
	# start_time = f"{getdate()} 00:00:00"
	# end_time= f"{getdate()} 23:59:59"
	page=1
	page_size=500

	requestUrl = f'''http://zkteco.alkhidmat.tech/iclock/api/transactions/?terminal_ip_address={terminal_ip_address}&emp_code={emp_code}&start_time={start_time}&end_time={end_time}&page={page}&page_size={page_size}'''
	# requestUrl = f'''
	# http://zkteco.alkhidmat.tech/iclock/api/transactions/?
 	# terminal_ip_address=192.168.19.106&
  	# emp_code=446&start_time=2025-06-2000:00:00&
   	# end_time=2025-06-26 23:59:59&page=1&page_size=100
	# '''
	# Optional: headers for authentication or content type
	headers = {
		"Authorization": "Token 73cc7ce918c9e7e36aaa1dc92282d1eb079cd82d",  # or use Basic auth
		"Content-Type": "application/json"
	}

	# Optional: query parameters
	params = {
		"limit": 10,
		"status": "active"
	}

	try:
		
		# Send GET request
		response = requests.get(requestUrl, headers=headers, params=params)

		# Raise exception if status code is not 200
		response.raise_for_status()

		# Parse JSON response
		data = response.json()
		
		# Print or use the data
		# print("Fetched Data:-----")
		datalist = data.get("data")
		# print(len(datalist))
		make_attendance_log(datalist, publish_progress=False)
		# if(len(datalist)>0):
		# 	frappe.enqueue(
		# 		make_attendance_log,
		# 		timeout=3000,
		# 		datalist = datalist,
		# 		publish_progress=False,
		# 	)
	except requests.exceptions.RequestException as e:
		frappe.log_error("RequestException:", e)
		print("RequestException:", e)
	

def make_attendance_log(datalist, publish_progress=False):
	terminal_ip_address = '10.0.7.201'
	attendance_list = []
	
	try:
		start_time = time.time()
		print(f'start_time {start_time}')
		print('--------------------------------')
		for row in datalist:
			row = frappe._dict(row)
			# print(row)
			print(f"emp_code: {row.emp_code}, date: {row.punch_time}")
			args = {
				"device_id": row.emp_code, # emp-code
				"device_ip": terminal_ip_address, # terminal_ip_address
				# "device_port": 4370, # terminal_ip_address
				# 'log_type': 'OUT' if(int(row.punch_state)) else 'IN',
				# 'log_from': 'Cron',
				'attendance_date': getdate(row.punch_time),
				'log': row.punch_time
			}
			# if(row.emp_code == "503"):
			if(frappe.db.exists('Employee', {"attendance_device_id": row.emp_code, 'status': 'Active'})):
				
				if(not frappe.db.exists('Attendance Log', args)):
					args.update({
						'doctype': 'Attendance Log',
						'log_type': 'OUT' if(int(row.punch_state)) else 'IN',
						'log_from': 'Cron',
					})
					attendance_list.append(args)
			
				
				# if(row.emp_code=="817"):
		print("-----------------------")
		
		print(len(attendance_list))
		# print((attendance_list))
		count = 0  # counter to track processed rows
		for cargs in attendance_list:
			doc = frappe.get_doc(cargs)
			doc.flags.ignore_validation=True
			doc.flags.ignore_permissions=True
			doc.insert()

			# increment counter
			count += 1
			
			# sleep after every 100 records
			if count % 200 == 0:
				print(f"-------------------------------------Processed {count} records, sleeping for 2 seconds...")
				time.sleep(2)  # change seconds as needed

	except RuntimeError as e:
		frappe.log_error("RuntimeError:", e)
		# print("RuntimeError:", e)
	except SyntaxError as e:
		frappe.log_error("SyntaxError:", e)
		# print("SyntaxError:", e)
	except Exception as e:
		frappe.log_error("Exception:", e)
		# print("====Exception:", e)

	end_time = time.time()
	print(f'end_time {end_time}')
	# print("<<--->>")
	print(f"Execution Time: {end_time - start_time:.4f} seconds")
	# print(args)
