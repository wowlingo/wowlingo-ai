CREATE TABLE IF NOT EXISTS `quest_item_units` (
  `quest_item_unit_id` int NOT NULL AUTO_INCREMENT,
  `type` varchar(20) NOT NULL COMMENT '유닛 타입',
  `str` text COMMENT '문자열',
  `url_normal` varchar(500) DEFAULT NULL COMMENT '일반 URL',
  `url_slow` varchar(500) DEFAULT NULL COMMENT '느린 URL',
  `remark` text COMMENT '비고',
  PRIMARY KEY (`quest_item_unit_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `quest_items` (
  `quest_item_id` int NOT NULL AUTO_INCREMENT,
  `quest_id` int NOT NULL,
  `type` varchar(20) NOT NULL COMMENT '문제 타입',
  `has_answer` tinyint NOT NULL DEFAULT '0' COMMENT '답변 여부',
  `question1` bigint DEFAULT NULL,
  `question2` bigint DEFAULT NULL,
  `answer1` bigint DEFAULT NULL COMMENT 'quest_item_unit 중 한가지의 id',
  `answer2` bigint DEFAULT NULL COMMENT 'quest_item_unit 중 한가지의 id, question과 동일한 값이 있어야함',
  `answer_sq` varchar(10) DEFAULT NULL COMMENT '평서문/의문문 답변',
  `answer_ox` varchar(10) DEFAULT NULL COMMENT 'Same/Different 답변',
  PRIMARY KEY (`quest_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `quests` (
  `quest_id` int NOT NULL AUTO_INCREMENT,
  `quest_item_count` smallint NOT NULL DEFAULT '0' COMMENT 'Quest Item 갯수',
  `order` smallint NOT NULL DEFAULT '0' COMMENT '순서',
  `title` varchar(100) NOT NULL COMMENT '문제집 타이틀',
  `type` varchar(100) NOT NULL COMMENT '문제집 타입',
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `created_by` varchar(50) DEFAULT NULL,
  `updated_by` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`quest_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `user` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `auth_type` varchar(20) NOT NULL COMMENT '인증 타입 (google, kakao, apple 등)',
  `auth` varchar(100) NOT NULL COMMENT '외부 인증 ID',
  `nickname` varchar(50) NOT NULL COMMENT '닉네임',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `user_quests` (
  `user_quest_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `quest_id` bigint NOT NULL,
  `done_yn` tinyint NOT NULL DEFAULT '0',
  `started_at` datetime NOT NULL,
  `ended_at` datetime DEFAULT NULL,
  `time_spent` int DEFAULT NULL,
  `progress_rate` smallint NOT NULL DEFAULT '0' COMMENT '진행률',
  `total_quest_item_count` int NOT NULL,
  `correct_quest_item_count` int DEFAULT '0',
  `accuracy_rate` decimal(5,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`user_quest_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `user_quest_items` (
  `user_quest_item_id` int NOT NULL AUTO_INCREMENT,
  `user_quest_id` int NOT NULL,
  `quest_item_id` bigint NOT NULL,
  `user_answer` text DEFAULT NULL COMMENT '선택한 답변 or Same/Different 답변 or 평서문/의문문 답변',
  `correct_yn` tinyint DEFAULT NULL,
  `time_spent` int DEFAULT NULL,
  `attempt_at` datetime DEFAULT NULL,
  `attempt_count` int DEFAULT '1',
  `started_at` datetime DEFAULT NULL,
  `ended_at` datetime DEFAULT NULL,
  PRIMARY KEY (`user_quest_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 샘플 데이터 삽입
-- ============================================

INSERT INTO wowlingo.quests
(quest_id, quest_item_count, `order`, title, `type`)
VALUES
(1, 10, 1, '2.1 평서문/의문문 억양 변별', 'statement-question'),
(2, 5, 2, '길이가 다른 낱말 변별', 'choice'),
(3, 3, 3, '2개의 소리 일치 여부 변별', 'same-different');


INSERT INTO wowlingo.quest_items
(quest_id, `type`, has_answer, question1, question2, question3, answer1, answer2, answer4, answer3, answer5, answer_sq, answer_ox, quest_item_id)
VALUES
(1, 'string', 1, 1, NULL, NULL, 1, -1, NULL, NULL, NULL, 'statement', NULL, 1),
(1, 'string', 1, 2, NULL, NULL, -1, 2, NULL, NULL, NULL, 'question', NULL, 2),
(1, 'string', 1, 3, NULL, NULL, 3, -1, NULL, NULL, NULL, 'statement', NULL, 3),
(1, 'string', 1, 4, NULL, NULL, 4, -1, NULL, NULL, NULL, 'statement', NULL, 4),
(1, 'string', 1, 5, NULL, NULL, -1, 5, NULL, NULL, NULL, 'question', NULL, 5),
(1, 'string', 1, 6, NULL, NULL, -1, 6, NULL, NULL, NULL, 'question', NULL, 6),
(1, 'string', 1, 7, NULL, NULL, 7, -1, NULL, NULL, NULL, 'statement', NULL, 7),
(1, 'string', 1, 8, NULL, NULL, -1, 8, NULL, NULL, NULL, 'question', NULL, 8),
(1, 'string', 1, 9, NULL, NULL, 9, -1, NULL, NULL, NULL, 'statement', NULL, 9),
(1, 'string', 1, 10, NULL, NULL, 10, -1, NULL, NULL, NULL, 'statement', NULL, 10),
(1, 'string', 1, 11, NULL, NULL, -1, 11, NULL, NULL, NULL, 'question', NULL, 11),
(1, 'string', 1, 12, NULL, NULL, -1, 12, NULL, NULL, NULL, 'question', NULL, 12),
(2, 'choice', 1, 13, NULL, NULL, 13, 14, NULL, NULL, NULL, 'word', NULL, 13), -- question과 answer가 같으면 정답
(2, 'choice', 1, 14, NULL, NULL, 14, 17, NULL, NULL, NULL, 'word', NULL, 14),
(2, 'choice', 1, 15, NULL, NULL, 22, 15, NULL, NULL, NULL, 'word', NULL, 15),
(2, 'choice', 1, 16, NULL, NULL, 16, 21, NULL, NULL, NULL, 'sentence', NULL, 16),
(2, 'choice', 1, 17, NULL, NULL, 24, 17, NULL, NULL, NULL, 'sentence', NULL, 17),
(3, 'same-different', 0, 18, 14, NULL, 18, -1, NULL, NULL, NULL, NULL, 'different', 18),
-- 들려줄 때 18 14를 연속으로 들려줘야 함? quest_item_id가 question과 answer에 들어가는게 여기서는 이상함
(3, 'same-different', 0, 19, 19, NULL, 19, -1, NULL, NULL, NULL, NULL, 'same', 19),
(3, 'same-different', 0, 20, 20, NULL, -1, 20, NULL, NULL, NULL, NULL, 'same', 20);


INSERT INTO wowlingo.quest_item_units
(quest_item_unit_id, `type`, str, url_normal, url_slow, remark)
VALUES
(1, 'statement', '감자', '/sounds/potato-normal.wav', '/sounds/potato-slow.wav', NULL),
(2, 'question', '고구마', '/sounds/sweetpotato.wav', '/sounds/sweetpotato-slow.wav', NULL),
(3, 'statement', '다리미', '/sounds/iron.wav', '/sounds/iron-slow.wav', NULL),
(4, 'statement', '도깨비', '/sounds/goblin.wav', '/sounds/goblin-slow.wav', NULL),
(5, 'question', '모래사장', '/sounds/sandybeach.wav', '/sounds/sandybeach-slow.wav', NULL),
(6, 'question', '미꾸라지', '/sounds/loach.wav', '/sounds/loach-slow.wav', NULL),
(7, 'statement', '감자', '/sounds/potato-normal.wav', '/sounds/potato-slow.wav', NULL),
(8, 'question', '고구마', '/sounds/sweetpotato.wav', '/sounds/sweetpotato-slow.wav', NULL),
(9, 'statement', '다리미', '/sounds/iron.wav', '/sounds/iron-slow.wav', NULL),
(10, 'statement', '도깨비', '/sounds/goblin.wav', '/sounds/goblin-slow.wav', NULL),
(11, 'question', '모래사장', '/sounds/sandybeach.wav', '/sounds/sandybeach-slow.wav', NULL),
(12, 'question', '미꾸라지', '/sounds/loach.wav', '/sounds/loach-slow.wav', NULL),

(13, 'word', '미꾸라지', '/sounds/loach.wav', '/sounds/loach-slow.wav', NULL),
(14, 'word', '도깨비', '/sounds/goblin.wav', '/sounds/goblin-slow.wav', NULL),
(15, 'word', '모래사장', '/sounds/sandybeach.wav', '/sounds/sandybeach-slow.wav', NULL),
(16, 'sentence', '감자', '/sounds/potato-normal.wav', '/sounds/potato-slow.wav', NULL),
(17, 'sentence', '고구마', '/sounds/sweetpotato.wav', '/sounds/sweetpotato-slow.wav', NULL),
(18, 'different', '모래사장', '/sounds/sandybeach.wav', '/sounds/sandybeach-slow.wav', NULL),
-- answer_ox의 type.... 어떻게 활용하는 거지? 그냥 word/sentence 인 것들을 quest_items로?
(19, 'sentence', '미꾸라지', '/sounds/loach.wav', '/sounds/loach-slow.wav', NULL),
(20, 'sentence', '도깨비', '/sounds/goblin.wav', '/sounds/goblin-slow.wav', NULL),
(21, 'sentence  ', '감자', '/sounds/potato-normal.wav', '/sounds/potato-slow.wav', NULL),
(22, 'word', '고구마', '/sounds/sweetpotato.wav', '/sounds/sweetpotato-slow.wav', NULL),
(23, 'word', '다리미', '/sounds/iron.wav', '/sounds/iron-slow.wav', NULL),
(24, 'word', '도깨비', '/sounds/goblin.wav', '/sounds/goblin-slow.wav', NULL);


INSERT INTO wowlingo.`user`
(user_id, auth_type, auth, nickname)
VALUES
(1, 'kakao', 'kakaoauth', 'guest');


CREATE TABLE `hashtags` (
  `code` varchar(16) NOT NULL COMMENT '해시태그 코드',
  `name` varchar(50) NOT NULL COMMENT '해시태그 문자열',
  `hashtag_id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`hashtag_id`)
) ENGINE=InnoDB;

CREATE TABLE `quest_hashtags` (
  `quest_id` bigint NOT NULL,
  `hashtag_id` bigint NOT NULL,
  `quest_hashtag_id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`quest_hashtag_id`)
) ENGINE=InnoDB;

CREATE TABLE `quest_item_unit_hashtags` (
  `quest_item_unit_hashtag_id` int NOT NULL AUTO_INCREMENT,
  `quest_item_unit_id` int NOT NULL,
  `hashtag_id` int DEFAULT NULL,
  PRIMARY KEY (`quest_item_unit_hashtag_id`),
  KEY `FK_654fc686765721611952995a90d` (`hashtag_id`),
  KEY `FK_c01c871e1339490d109784894b6` (`quest_item_unit_id`),
  CONSTRAINT `FK_654fc686765721611952995a90d` FOREIGN KEY (`hashtag_id`) REFERENCES `hashtags` (`hashtag_id`),
  CONSTRAINT `FK_c01c871e1339490d109784894b6` FOREIGN KEY (`quest_item_unit_id`) REFERENCES `quest_item_units` (`quest_item_unit_id`)
) ENGINE=InnoDB;


CREATE TABLE `user_quest_attempts` (
  `login_date` timestamp NOT NULL COMMENT '로그인 날짜',
  `attempt_date` timestamp NULL DEFAULT NULL COMMENT '학습 시도 날짜',
  `ai_feedback_id` bigint DEFAULT NULL COMMENT 'AI 피드백 Id',
  `user_quest_attempt_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  PRIMARY KEY (`user_quest_attempt_id`),
  KEY `FK_a37c6437085c74c17e2ef7456c1` (`user_id`),
  CONSTRAINT `FK_a37c6437085c74c17e2ef7456c1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB;


CREATE TABLE `vocab_hashtags` (
  `vocab_hashtag_id` int NOT NULL AUTO_INCREMENT,
  `hashtag_id` int NOT NULL,
  `vocab_id` int NOT NULL,
  PRIMARY KEY (`vocab_hashtag_id`),
  KEY `FK_61623e7a3c05b99d9ae8699e66c` (`hashtag_id`),
  KEY `FK_04f465b0f10f635470a52550e40` (`vocab_id`),
  CONSTRAINT `FK_04f465b0f10f635470a52550e40` FOREIGN KEY (`vocab_id`) REFERENCES `vocabulary` (`vocab_id`),
  CONSTRAINT `FK_61623e7a3c05b99d9ae8699e66c` FOREIGN KEY (`hashtag_id`) REFERENCES `hashtags` (`hashtag_id`)
) ENGINE=InnoDB;


CREATE TABLE `vocabulary` (
  `user_id` bigint NOT NULL,
  `url_normal` varchar(500) NOT NULL COMMENT '일반 url',
  `created_at` timestamp NOT NULL,
  `slow_normal` varchar(500) NOT NULL COMMENT '느린 url',
  `vocab_id` int NOT NULL AUTO_INCREMENT,
  `str` varchar(50) NOT NULL COMMENT '문자열',
  PRIMARY KEY (`vocab_id`)
) ENGINE=InnoDB;

CREATE TABLE `ai_feedbacks` (
  `ai_feedback_id` bigint NOT NULL AUTO_INCREMENT,
  `user_quest_attempt_id` bigint NOT NULL COMMENT '사용자 문제 이력 달력 id',
  `created_at` timestamp NULL DEFAULT NULL COMMENT 'AI 생성 날짜',
  `message` varchar(100) DEFAULT NULL COMMENT '오늘은 20문제 중 15개나 맞추셨어요',
  `detail` varchar(500) DEFAULT NULL COMMENT '모음 구분은 매우 잘하셨고, 특히 동물 단어에서 90% 이상의 정답률을 기록했습니다.',
  `tags` varchar(500) DEFAULT NULL COMMENT '#성공적, #높은정답률, #듣기능력향상',
  PRIMARY KEY (`ai_feedback_id`)
) ENGINE=InnoDB;


INSERT INTO wowlingo.hashtags
(code, name, hashtag_id)
VALUES('code1', '환경음', 1),
('code2', '말소리', 2),
('code3', '의문문', 3),
('code4', '평서문', 4),
('code5', '3-4 음절 단어', 5),
('code6', '2-3 음정 단어', 6),
('code7', '1-4 어절 문장', 7),
('code8', '2-4 어절 문장', 8),
('code9', '음향 패턴 다른', 9),
('code10', '음향 패턴 유사', 10),
('code11', '문장', 11);
