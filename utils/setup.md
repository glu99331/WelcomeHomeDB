# Alternate setup instructions

## Create user with password
`CREATE USER 'welcomehomeadmin'@'localhost' IDENTIFIED BY '1234';`

## Grant all privileges on WelcomeHomeDB to the user
`GRANT ALL PRIVILEGES ON WelcomeHomeDB.* TO 'welcomehomeadmin'@'localhost';`

## Grant FILE privilege for handling images
`GRANT FILE ON *.* TO 'welcomehomeadmin'@'localhost';`

## Apply the privileges
`FLUSH PRIVILEGES;`

## Image upload instructions
- You need to have an `images` directory outside i.e. parallel to your git repo. And that should have all the images.

## DB config instructions
- You need to have `config.py` file outside of your git repo in a folder called `instance` such that the `instance` folder would be parallel to your git repo.