CREATE TABLE IF NOT EXISTS student (
username VARCHAR(32) PRIMARY KEY,
password VARCHAR(32) NOT NULL
);

INSERT INTO student (username, password) VALUES ('yutaro', 'cee1694a17cc52810875285180e22884');

CREATE TABLE sessions (
    session_num CHAR(36) PRIMARY KEY,
    started_at DATETIME NOT NULL,
    username VARCHAR(32),
    FOREIGN KEY (username) REFERENCES student(username)
);

CREATE TABLE tasks (
    aid INT,
    tid INT,
    title VARCHAR(255),
    PRIMARY KEY (aid, tid)
);
INSERT INTO tasks (aid, tid, title) VALUES (1, 1, 'Task11');

CREATE TABLE submissions (
    username VARCHAR(32),
    aid INT,
    tid INT,
    code VARCHAR(5000),
    submitted_at DATETIME,
    PRIMARY KEY (username, aid, tid),
    FOREIGN KEY (username) REFERENCES student(username),
    FOREIGN KEY (aid, tid) REFERENCES tasks(aid, tid)
);