#[Unit]
#Description=AKFP Service
#After=multi-user.target
#StartLimitIntervalSec=300
#StartLimitBurst=5

#[Service]
#WorkingDirectory=/home/ubuntu/frappe-alkhidmat
#User=ubuntu
#Type=simple
#ExecStart=/usr/bin/python3 /home/ubuntu/frappe-alkhidmat/apps/akf_hrms/akf_hrms/services/live_capture/live_akfp.py &> /dev/null
#ExecStart=/usr/bin/python3 /home/ubuntu/frappe-alkhidmat/apps/akf_hrms/akf_hrms/services/live_capture/live_akfp.py
#StandardOutput=append:/var/log/live_akfp_service.log
#StandardError=append:/var/log/live_akfp_service.log
#ExecStart=/usr/bin/python3 /home/ubuntu/frappe-alkhidmat/apps/akf_hrms/akf_hrms/services/live_capture/live_akfp.py >> /var/log/akfp_service.log 2>&1
#ExecStart=/usr/bin/python3 /home/ubuntu/frappe-alkhidmat/apps/akf_hrms/akf_hrms/services/live_capture/live_akfp.py &> /dev/null
#Restart=on-failure
#RestartSec=10
#[Install]
#WantedBy=multi-user.target
[Unit]
Description=AKFP Service
After=multi-user.target

[Service]
WorkingDirectory=/home/master/Frappe-alkhidmat
User=master
Group=master
Type=simple
ExecStart=/usr/bin/python3 /home/master/Frappe-alkhidmat/apps/akf_hrms/akf_hrms/services/live_capture/live_akfp.py
StandardOutput=append:/var/log/live_akfp_service.log
StandardError=append:/var/log/live_akfp_service.log
#SyslogIdentifier=live_akfp
Restart=always
RestartSec=10
LimitNOFILE=65536
TimeoutStartSec=30
#TimeoutStopSec=30

[Install]
WantedBy=multi-user.target


"OPEN TERMINAL:

sudo apt-get install -y systemd
systemd --version
sudo nano /lib/systemd/system/test.service (name of the service which is test in this case)


> CREATE SERVICE FILE E.G; example.service
> enter below info update your service path

sudo systemctl daemon-reload
sudo systemctl enable akfp_central_office.service
sudo systemctl start akfp_central_office.service

sudo systemctl stop akfp_central_office.service
sudo systemctl restart akfp_central_office.service
sudo systemctl status akfp_central_office.service