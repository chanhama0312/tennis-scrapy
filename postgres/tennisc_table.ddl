CREATE TABLE toei_court
(court_name VARCHAR(30) NOT NULL,
month_day VARCHAR(10) NOT NULL,
dotw VARCHAR(5) NOT NULL,
start_time VARCHAR(10) NOT NULL,
free_num INTEGER NOT NULL,
CONSTRAINT upst_pkey PRIMARY KEY (court_name,month_day,start_time));

CREATE TABLE notification_court
(court_name VARCHAR(30) NOT NULL,
dotw VARCHAR(5) NOT NULL,
start_time VARCHAR(10) NOT NULL,
CONSTRAINT noti_pkey PRIMARY KEY (court_name));
