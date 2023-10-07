CREATE TABLE `examples`  (
  `example` varchar(255) NOT NULL,
  PRIMARY KEY (`example`)
);

CREATE TABLE `meanings`  (
  `meaning` varchar(255) NOT NULL,
  `note` varchar(255) NULL,
  PRIMARY KEY (`meaning`)
);

CREATE TABLE `pos`  (
  `pos` varchar(255) NOT NULL,
  PRIMARY KEY (`pos`)
);

CREATE TABLE `relAntonym`  (
  `relWordMeaningId` int NOT NULL,
  `antonym` varchar(255) NOT NULL
);

CREATE TABLE `relDerivative`  (
  `relWordMeaningId` int NOT NULL,
  `derivative` varchar(255) NOT NULL
);

CREATE TABLE `relExample`  (
  `relWordMeaningId` int NOT NULL,
  `example` varchar(255) NOT NULL
);

CREATE TABLE `relSimilarWords`  (
  `word` varchar(255) NOT NULL,
  `similarWord` varchar(255) NOT NULL
);

CREATE TABLE `relSynonyms`  (
  `relWordMeaningId` int NOT NULL,
  `synonyms` varchar(255) NOT NULL
);

CREATE TABLE `relWordMeaning`  (
  `relWordMeaningId` int NOT NULL AUTO_INCREMENT,
  `word` varchar(255) NOT NULL,
  `pos` varchar(255) NOT NULL,
  `meaning` varchar(255) NOT NULL,
  PRIMARY KEY (`relWordMeaningId`)
);

CREATE TABLE `words`  (
  `word` varchar(255) NOT NULL,
  `last_review_date` date NULL,
  `review_times` int NULL,
  `forget_times` int NULL,
  PRIMARY KEY (`word`)
);

ALTER TABLE `relAntonym` ADD CONSTRAINT `fk_relAntonym_relWordMeaning_1` FOREIGN KEY (`relWordMeaningId`) REFERENCES `relWordMeaning` (`relWordMeaningId`);
ALTER TABLE `relAntonym` ADD CONSTRAINT `fk_relAntonym_words_1` FOREIGN KEY (`antonym`) REFERENCES `words` (`word`);
ALTER TABLE `relDerivative` ADD CONSTRAINT `fk_relDerivative_relWordMeaning_1` FOREIGN KEY (`relWordMeaningId`) REFERENCES `relWordMeaning` (`relWordMeaningId`);
ALTER TABLE `relDerivative` ADD CONSTRAINT `fk_relDerivative_words_1` FOREIGN KEY (`derivative`) REFERENCES `words` (`word`);
ALTER TABLE `relExample` ADD CONSTRAINT `fk_relExample_relWordMeaning_1` FOREIGN KEY (`relWordMeaningId`) REFERENCES `relWordMeaning` (`relWordMeaningId`);
ALTER TABLE `relExample` ADD CONSTRAINT `fk_relExample_examples_1` FOREIGN KEY (`example`) REFERENCES `examples` (`example`);
ALTER TABLE `relSimilarWords` ADD CONSTRAINT `fk_relSimilarWords_words_1` FOREIGN KEY (`word`) REFERENCES `words` (`word`);
ALTER TABLE `relSimilarWords` ADD CONSTRAINT `fk_relSimilarWords_words_2` FOREIGN KEY (`similarWord`) REFERENCES `words` (`word`);
ALTER TABLE `relSynonyms` ADD CONSTRAINT `fk_relSynonyms_relWordMeaning_1` FOREIGN KEY (`relWordMeaningId`) REFERENCES `relWordMeaning` (`relWordMeaningId`);
ALTER TABLE `relSynonyms` ADD CONSTRAINT `fk_relSynonyms_words_1` FOREIGN KEY (`synonyms`) REFERENCES `words` (`word`);
ALTER TABLE `relWordMeaning` ADD CONSTRAINT `fk_relWordMeaning_words_1` FOREIGN KEY (`word`) REFERENCES `words` (`word`);
ALTER TABLE `relWordMeaning` ADD CONSTRAINT `fk_relWordMeaning_pos_1` FOREIGN KEY (`pos`) REFERENCES `pos` (`pos`);
ALTER TABLE `relWordMeaning` ADD CONSTRAINT `fk_relWordMeaning_meanings_1` FOREIGN KEY (`meaning`) REFERENCES `meanings` (`meaning`);

