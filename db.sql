use rasa_voicebot;

drop table if exists CustomUser;
create table CustomUser(
	id int primary key auto_increment not null,
    username varchar(20) not null,
    pass varchar(16) not null,
    firstname nvarchar(50) not null,
    lastname nvarchar(50),
    dob datetime,
    gender nvarchar(20),
    email varchar(100),
    last_logged datetime,
    date_created datetime not null default now(),
    is_active boolean not null default true
);

drop table if exists MySchedule;
create table MySchedule(
	id int primary key auto_increment not null,
    date_ date not null,
    start_time time not null,
    end_time time,
    content nvarchar(200) not null,
    location nvarchar(200),
    date_created datetime not null default now(),
    last_modified datetime not null default now(),
    is_active boolean not null default true,
    
    -- recurrrent fields
    is_recurring boolean not null default false,
    recurring_type varchar(50),
    separation_count int default 1,
    max_number_of_occurrences int,
    recurrence_end_date date,
    
    -- relation fields
    parent_id int default 0,
    user_id int
    -- foreign key (user_id) references CustomUser(id)
);

-- create table ScheduleRecurrentPattern(
-- 	schedule_id int primary key not null,
--     recurring_type varchar(50) not null,
--     constraint chk_recurring_type check (recurring_type in ('daily', 'weekly', 'monthly', 'yearly')),
--     separation_count int not null default 1,
--     max_number_of_occurences int,
--     is_active boolean not null default true,
--     date_created datetime not null default now(),
--     last_modified datetime
-- );

drop table if exists ScheduleInstanceException;
create table ScheduleInstanceException(
	id int primary key not null auto_increment,
    schedule_id int not null,
    -- foreign key (schedule_id) references MySchedule(id),
    is_rescheduled boolean,
    is_cancelled boolean,
    date_ date not null,
    start_time time,
    end_time time,
    content nvarchar(200),
    location nvarchar(200),
    user_id int,
    date_created datetime not null default now(),
    last_modified datetime,
    is_active boolean not null default true
);


drop table if exists Reminder;
create table Reminder(
	id int primary key not null auto_increment,
    date_ date not null,
    time_ time,
    content nvarchar(200) not null,
    
    -- recurrent fields
    is_recurring boolean not null default false,
    recurrence_end_date date,
    recurring_type varchar(50),
    separation_count int default 1,
    max_number_of_occurrences int,
    
    is_active boolean not null default true,
    date_created datetime not null default now(),
    last_modified datetime,
    user_id int
    -- foreign key (user_id) references CustomUser(id)
);

-- create table ReminderRecurrentPattern(
-- 	reminder_id int primary key not null,
--     recurring_type varchar(50) not null,
--     constraint chk_recurring_type_reminder check (recurring_type in ('daily', 'weekly', 'monthly', 'yearly')),
--     separation_count int not null default 1,
--     max_number_of_occurences int,
--     is_active boolean not null default true,
--     date_created datetime not null default now(),
--     last_modified datetime
-- );

drop table if exists ReminderInstanceException;
create table ReminderInstanceException(
	id int primary key not null auto_increment,
    reminder_id int not null,
    -- foreign key (schedule_id) references MySchedule(id),
    is_edited boolean,
    is_deleted boolean,
    date_ date not null,
    time_ time not null,
    content nvarchar(200) not null,
    user_id int,
    date_created datetime not null default now(),
    last_modified datetime,
    is_active boolean not null default true
);

drop table if exists Task;
create table Task(
	id int primary key not null auto_increment,
    date_ date not null,
    time_ time,
    content nvarchar(200) not null,
    user_id int,
    is_active boolean not null default true,
    date_created datetime not null default now(),
    last_modified datetime
);

drop table if exists Contact;
create table Contact(
	id int primary key not null auto_increment,
    owner_id int,
    name_ nvarchar(200) not null,
    email varchar(200),
    dob date,
    description_ nvarchar(200),
    contact_detail varchar(200),
    date_created datetime not null default now(),
    last_modified datetime,
    is_active boolean not null default true
);

