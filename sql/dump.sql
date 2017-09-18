-- MySQL dump 10.13  Distrib 5.7.19, for osx10.12 (x86_64)
--
-- Host: localhost    Database: notificationbot
-- ------------------------------------------------------
-- Server version	5.7.19

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
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notificationbot_channels`
--

LOCK TABLES `notificationbot_channels` WRITE;
/*!40000 ALTER TABLE `notificationbot_channels` DISABLE KEYS */;
INSERT INTO `notificationbot_channels` VALUES (1,'334898180154195971','london-raids-3'),(2,'272445393995038721','london-all_sightings'),(3,'284161023135580181','london-rares'),(4,'307699757659324416','london-ultra-rares'),(5,'334898831516893184','london-raids-4'),(6,'335417354894835713','london-raids-1_2'),(7,'337970455736614913','london-raids-legendary'),(8,'352096637008478219','london-dt-sightings'),(10,'284905790123409409','testing_grounds');
/*!40000 ALTER TABLE `notificationbot_channels` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notificationbot_keywords`
--

LOCK TABLES `notificationbot_keywords` WRITE;
/*!40000 ALTER TABLE `notificationbot_keywords` DISABLE KEYS */;
INSERT INTO `notificationbot_keywords` VALUES (2,'tyranitar','341730842303004673',1,1),(6,'unown','341730842303004673',0,1),(9,'magikarp','308720902827409409',0,1),(10,'gyarados','308720902827409409',0,1),(11,'unown','205342915034087424',0,1),(12,'jackson','205342915034087424',0,1),(13,'blissey','205342915034087424',0,1),(14,'tyranitar','205342915034087424',0,1),(15,'dragonite','205342915034087424',0,1),(17,'dugtrio','308720902827409409',0,1),(18,'grimer','341730842303004673',1,0);
/*!40000 ALTER TABLE `notificationbot_keywords` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=latin1 COMMENT='All the user roles with their respective powers';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notificationbot_roles`
--

LOCK TABLES `notificationbot_roles` WRITE;
/*!40000 ALTER TABLE `notificationbot_roles` DISABLE KEYS */;
INSERT INTO `notificationbot_roles` VALUES (4,'322740968942075914','Donor-Lnd',1,1),(5,'282517299070763009','Admin',1,1),(8,'301346383183609856','Code Commander',1,1),(10,'293540247294312448','Chat-Mods',1,1),(11,'345583835901329408','bot-commander',1,1);
/*!40000 ALTER TABLE `notificationbot_roles` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-09-18 13:49:13
