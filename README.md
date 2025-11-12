### Attendance Module

The Attendance Module is a core component of the Human Resource Management System (HRMS) that enables organizations to efficiently track, manage, and analyze employee attendance, working hours, and time-off records. It provides a centralized platform to record employee presence, leaves, and absenteeism while integrating seamlessly with payroll and performance systems.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app attendance_module
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/attendance_module
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
