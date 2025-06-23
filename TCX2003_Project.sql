CREATE TABLE IF NOT EXISTS students (
username VARCHAR(10) NOT NULL PRIMARY KEY,
password_hash VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
session_num INT PRIMARY KEY,
username VARCHAR(10),
started_at DATETIME,
FOREIGN KEY (username) REFERENCES students(username)
);

CREATE TABLE IF NOT EXISTS assessments (
a_id INT PRIMARY KEY,
title VARCHAR(256),
due_date DATETIME
);

CREATE TABLE IF NOT EXISTS tasks (
t_id INT PRIMARY KEY,
a_id INT,
title VARCHAR(256),
FOREIGN KEY (a_id) REFERENCES assessments(a_id)
);

CREATE TABLE IF NOT EXISTS submissions (
submission_id INT PRIMARY KEY,
username VARCHAR(10),
a_id INT,
t_id INT,
codebase VARCHAR(1024),
submit_at DATETIME,
attempt_number INT,
score INT,
FOREIGN KEY (username) REFERENCES students(username),
FOREIGN KEY (a_id) REFERENCES assessments(a_id),
FOREIGN KEY (t_id) REFERENCES tasks(a_id)
);

DELIMITER //

CREATE PROCEDURE `create_student`(
    IN p_username VARCHAR(50),     
    IN p_password VARCHAR(255),    
    OUT p_errorMessage VARCHAR(255)
)
BEGIN
    
    DECLARE is_error BOOLEAN DEFAULT FALSE;
    DECLARE local_error_message VARCHAR(255); 

    
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET is_error = TRUE;
        GET DIAGNOSTICS CONDITION 1 local_error_message = MESSAGE_TEXT;

        SET p_errorMessage = CONCAT('Error creating user: ', local_error_message);

        ROLLBACK;
    END;

    START TRANSACTION;
    INSERT INTO students (username, password) VALUES (p_username, p_password);

    SET p_errorMessage = 'User created successfully.';
    
    COMMIT;

END //

DELIMITER ;