-- Schema for NCBI Lookup database.  

-- Name of database
USE NCBI;

-- The Gi_Info table caches information about GI numbers
-- pulled down from NCBI.
CREATE TABLE Gi_Info(
        -- Unique ID for this Gi
        Gi_Info_ID INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	-- Unique Gi
        Gi INT UNSIGNED UNIQUE,
	-- String title of this GI
	Title TEXT,
        -- Taxonomy ID related to this GI
        Tax_ID INT UNSIGNED,
        -- Length of the sequence for this GI
        Length FLOAT UNSIGNED,
	-- NCBI Taxon_Id for the family this Gi belongs to
	Family_Tax_ID INT UNSIGNED,
	-- NCBI Taxon_Id for the genus this Gi belongs to
	Genus_Tax_ID INT UNSIGNED,
	-- NCBI Taxon_Id for the species this Gi belongs to
	Species_Tax_ID INT UNSIGNED,
	-- Keys on the taxon levels
	KEY Family (Family_Tax_ID),
	KEY Genus (Genus_Tax_ID),
	KEY Species (Species_Tax_ID))
        ENGINE=InnoDB;

-- The NCBI_Lock table is used as a lock file
-- for NCBI lookup throttling.
CREATE TABLE NCBI_Lock(
        -- This simply records the last time an NCBI 
	-- Lookup was performed.
        Last_Lookup DATETIME PRIMARY KEY)
        ENGINE=InnoDB;
