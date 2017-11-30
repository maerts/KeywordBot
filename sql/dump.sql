-- MySQL dump 10.13  Distrib 5.7.20, for Linux (x86_64)
--
-- Host: localhost    Database: notificationbot
-- ------------------------------------------------------
-- Server version	5.7.20-0ubuntu0.16.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `notificationbot_channels`
--

DROP TABLE IF EXISTS `notificationbot_channels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notificationbot_channels` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `channel_id` varchar(50) DEFAULT NULL,
  `channel_name` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `channel_id` (`channel_id`),
  KEY `channel_name` (`channel_name`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notificationbot_coord`
--

DROP TABLE IF EXISTS `notificationbot_coord`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notificationbot_coord` (
  `discord_id` bigint(20) NOT NULL,
  `lng` decimal(25,15) DEFAULT NULL,
  `lat` decimal(25,15) DEFAULT NULL,
  `km` int(11) DEFAULT NULL,
  PRIMARY KEY (`discord_id`),
  UNIQUE KEY `discord_id_UNIQUE` (`discord_id`),
  KEY `discord_id_index` (`discord_id`),
  KEY `lng_index` (`lng`),
  KEY `lat_index` (`lat`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notificationbot_iv`
--

DROP TABLE IF EXISTS `notificationbot_iv`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notificationbot_iv` (
  `discord_id` bigint(20) unsigned NOT NULL,
  `iv` int(11) DEFAULT NULL,
  PRIMARY KEY (`discord_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notificationbot_keywords`
--

DROP TABLE IF EXISTS `notificationbot_keywords`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notificationbot_keywords` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `keyword` varchar(100) DEFAULT NULL,
  `discord_id` varchar(50) DEFAULT NULL,
  `raid` tinyint(4) DEFAULT '0',
  `spawn` tinyint(4) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `keyword` (`keyword`),
  KEY `discord_id` (`discord_id`)
) ENGINE=InnoDB AUTO_INCREMENT=509 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notificationbot_levenshtein`
--

DROP TABLE IF EXISTS `notificationbot_levenshtein`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notificationbot_levenshtein` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `pokemon` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `pokemon` (`pokemon`)
) ENGINE=InnoDB AUTO_INCREMENT=803 DEFAULT CHARSET=latin1 COMMENT='The dictionary table for pokemon names';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notificationbot_roles`
--

DROP TABLE IF EXISTS `notificationbot_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notificationbot_roles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `roleid` varchar(55) DEFAULT NULL,
  `rolename` varchar(100) DEFAULT NULL,
  `user` tinyint(4) DEFAULT '0',
  `admin` tinyint(4) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`),
  KEY `roleid` (`roleid`),
  KEY `rolename` (`rolename`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=latin1 COMMENT='All the user roles with their respective powers';
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-11-30 16:29:14
