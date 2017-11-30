CREATE TABLE `notificationbot_cp` (
  `discord_id` bigint(20) unsigned NOT NULL,
  `cp` int(11) DEFAULT NULL,
  PRIMARY KEY (`discord_id`) ) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `notificationbot_lvl` (
  `discord_id` bigint(20) unsigned NOT NULL,
  `lvl` int(11) DEFAULT NULL,
  PRIMARY KEY (`discord_id`) ) ENGINE=InnoDB DEFAULT CHARSET=latin1;
