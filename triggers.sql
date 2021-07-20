use rasa_voicebot;

delimiter $$
create trigger schedule_recurrence_end_date before insert on MySchedule
for each row
begin
	declare date_diff int;
    set date_diff = 0;
    
	if new.max_number_of_occurrences is not null then
		if new.recurring_type = 'daily' then
			set date_diff = 1 * new.separation_count * new.max_number_of_occurrences;
			set new.recurrence_end_date = date_add(new.date_, interval date_diff day);
        end if;
        
        if new.recurring_type = 'weekly' then
			set date_diff = 7 * new.separation_count * new.max_number_of_occurrences;
            set new.recurrence_end_date = date_add(new.date_, interval date_diff day);
        end if;
        
        if new.recurring_type = 'monthly' then
			set date_diff = 1 * new.separation_count * new.max_number_of_occurrences;
            set new.recurrence_end_date = date_add(new.date_, interval date_diff month);
        end if;
        
        if new.recurring_type = 'yearly' then
			set date_diff = 1 * new.separation_count * new.max_number_of_occurrences;
            set new.recurrence_end_date = date_add(new.date_, interval date_diff year);
        end if;
    end if;
end$$

create trigger schedule_exception before insert on ScheduleInstanceException
for each row
begin
	-- declare start_time time;
--     declare end_time time;
--     declare content nvarchar(200);
--     declare location nvarchar(200);
    
    select start_time, end_time, content, location
    into @start_time, @end_time, @content, @location
    from MySchedule
    where MySchedule.id = new.schedule_id
    limit 1;
    
    set new.start_time = @start_time;
    set new.end_time = @end_time;
    set new.content = @content;
    set new.location = @location;
end$$
delimiter ;


drop trigger if exists reminder_recurrence_end_date;
drop trigger if exists reminder_exception;
delimiter $$
create trigger reminder_recurrence_end_date before insert on Reminder
for each row
begin
	declare date_diff int;
    set date_diff = 0;
    
	if new.max_number_of_occurrences is not null then
		if new.recurring_type = 'daily' then
			set date_diff = 1 * new.separation_count * new.max_number_of_occurrences;
			set new.recurrence_end_date = date_add(new.date_, interval date_diff day);
        end if;
        
        if new.recurring_type = 'weekly' then
			set date_diff = 7 * new.separation_count * new.max_number_of_occurrences;
            set new.recurrence_end_date = date_add(new.date_, interval date_diff day);
        end if;
        
        if new.recurring_type = 'monthly' then
			set date_diff = 1 * new.separation_count * new.max_number_of_occurrences;
            set new.recurrence_end_date = date_add(new.date_, interval date_diff month);
        end if;
        
        if new.recurring_type = 'yearly' then
			set date_diff = 1 * new.separation_count * new.max_number_of_occurrences;
            set new.recurrence_end_date = date_add(new.date_, interval date_diff year);
        end if;
    end if;
end$$

create trigger reminder_exception before insert on ReminderInstanceException
for each row
begin
	select time_, content
    into @time_, @content
    from Reminder
    where Reminder.id = new.reminder_id
    limit 1;
    
    set new.time_ = @time_;
    set new.content = @content;
end$$
delimiter ;