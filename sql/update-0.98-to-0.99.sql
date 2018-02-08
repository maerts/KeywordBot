ALTER TABLE `notificationbot_iv` 
ADD COLUMN `force` INT NULL DEFAULT 0 AFTER `iv`;

ALTER TABLE `notificationbot_cp` 
ADD COLUMN `force` INT NULL DEFAULT 0 AFTER `cp`;

ALTER TABLE `notificationbot_lvl` 
ADD COLUMN `force` INT NULL DEFAULT 0 AFTER `lvl`;
