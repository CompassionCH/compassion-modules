To configure this module, go in **Attendances/Configuration/Attendance Settings**:

#. You can configure a *free break* time that is offered to employees. It means this time will count as a break time
   but won't be deduced from the attendance of the employees.
#. You can configure a *maximum extra hours limit*. When the employee makes more extra hours than the limit,
   it doesn't increase anymore his extra hours balance. This module offers to disable this continuous limit for some
   employee via the *continuous extra hours computation* flag in Employee. When unset, the limit will only be enforced
   once per year.
#. In **Attendances/Configuration/Break rules**  you can define a minimum break time required per day based on how many
   hours the employee worked on the day.
   Total break is the total break time the employee must do per day
   Minimum break is the minimum time required for at least one break (for instance if the employee should take at least
   30 minutes of break for lunch)
#. In **Attendances/Configuration/Coefficient** you can define special days that will give more extra hours to the
   employee. For instance you could set the Sunday to count 1.5x time. You can limit those rules to specific categories
   of employees.
#. In **Attendances/Manage Attendances/Employee** you can setup the *initial balance* of each employee,
   when you start using the module to count the hours.
   Just go in one employee, under the Hours tab, and set the value. The value will be updated each year to avoid
   computing over more than one year of attendances.
#. In **Attendances/Manage Attendances/Employee** you can setup a *continuous extra hours computation* for each employee.
   When unset, this allows the employee to get over the max_extra_hours limit. The max_extra_hours will however be enforced
   at the annual hours computation. The date of this computation can be set in *Attendance/Configuration/Next Balance Cron
   Execution*.
#. In **Employee/Contracts/Working Schedule** configure the working schedule of each employee by going to the
   *resource.calendar* object
#. In **Leaves/Configuration/Leave Types** configure if leave types should not deduce from the due hours of
   the employees by setting *Keep due hours*

To configure the cron which updates the balance of employees annually, go in **Settings/Technical/Automation/Automated Actions**:

#. In the cron *Compute annual extra hours balance* choose the scheduled date on which you want to apply the process to move the
   extra hours of employees in their annual balance and cap off the extra hours of employee with an annual extra hours
   computation. This is typically done at the beginning of the year. This process avoids the system to compute a huge amount of
   data after a few years of attendance.
