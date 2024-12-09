# Alternate setup instructions

## Create user with password
`CREATE USER 'welcomehomeadmin'@'localhost' IDENTIFIED BY '1234';`

## Grant all privileges on WelcomeHomeDB to the user
`GRANT ALL PRIVILEGES ON WelcomeHomeDB.* TO 'welcomehomeadmin'@'localhost';`

## Grant FILE privilege for handling images
`GRANT FILE ON *.* TO 'welcomehomeadmin'@'localhost';`

## Apply the privileges
`FLUSH PRIVILEGES;`