
CREATE TABLE Person (
  username VARCHAR(32),
  password VARCHAR(64),
  firstName VARCHAR(32),
  lastName VARCHAR(32),
  email VARCHAR(32),
  PRIMARY KEY (username)
);

CREATE TABLE Photo (
  pID INT AUTO_INCREMENT,
  postingDate DATETIME,
  filePath VARCHAR(255),
  allFollowers INT,
  caption VARCHAR(1000),
  poster VARCHAR(32),
  PRIMARY KEY (pID),
  FOREIGN KEY (poster) REFERENCES Person (username)
);

CREATE TABLE FriendGroup (
  groupName VARCHAR(32),
  groupCreator VARCHAR(32),
  description VARCHAR(1000),
  PRIMARY KEY (groupName, groupCreator),
  FOREIGN KEY (groupCreator) REFERENCES Person (username)
);

CREATE TABLE ReactTo (
  username VARCHAR(32),
  pID INT,
  reactionTime DATETIME,
  comment VARCHAR(1000),
  emoji VARCHAR(32), -- you may replace this by a BLOB or fileName of a jpg or some such
	PRIMARY KEY (username, pID),
  FOREIGN KEY (pID) REFERENCES Photo (pID),
  FOREIGN KEY (username) REFERENCES Person (username)
);

CREATE TABLE Tag (
  pID INT,
  username VARCHAR(32),
  tagStatus INT,
	PRIMARY KEY (pID, username),
  FOREIGN KEY (pID) REFERENCES Photo (pID),
  FOREIGN KEY (username) REFERENCES Person (username)
);


CREATE TABLE SharedWith (
  pID INT,
  groupName VARCHAR(32),
  groupCreator VARCHAR(32),
	PRIMARY KEY (pID, groupName, groupCreator),
	FOREIGN KEY (groupName, groupCreator) REFERENCES FriendGroup(groupName, groupCreator),
  FOREIGN KEY (pID) REFERENCES Photo (pID)
);



CREATE TABLE BelongTo (
  username VARCHAR(32),
  groupName VARCHAR(32),
	groupCreator VARCHAR(32),
  PRIMARY KEY (username, groupName, groupCreator),
  FOREIGN KEY (username) REFERENCES Person (username),
  FOREIGN KEY (groupName, groupCreator) REFERENCES FriendGroup (groupName, groupCreator)
);

CREATE TABLE Follow (
  follower VARCHAR(32),
  followee VARCHAR(32),
  followStatus INT,
  PRIMARY KEY (follower, followee),
  FOREIGN KEY (follower) REFERENCES Person (username),
  FOREIGN KEY (followee) REFERENCES Person (username)
);
