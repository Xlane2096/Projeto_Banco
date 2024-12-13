-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8mb3 ;
USE `mydb` ;

-- -----------------------------------------------------
-- Table `mydb`.`cliente`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`cliente` (
  `idcliente` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(45) NOT NULL,
  `nif` INT NOT NULL,
  `iban` INT NOT NULL,
  `país` VARCHAR(10) NULL DEFAULT NULL,
  PRIMARY KEY (`idcliente`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mydb`.`conta`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`conta` (
  `idconta` INT NOT NULL AUTO_INCREMENT,
  `idcliente` VARCHAR(45) NOT NULL,
  `dataabertura` VARCHAR(45) NOT NULL,
  `saldo` FLOAT NOT NULL,
  `cliente_idcliente` INT NOT NULL,
  PRIMARY KEY (`idconta`, `cliente_idcliente`),
  INDEX `fk_conta_cliente_idx` (`cliente_idcliente` ASC) VISIBLE,
  CONSTRAINT `fk_conta_cliente`
    FOREIGN KEY (`cliente_idcliente`)
    REFERENCES `mydb`.`cliente` (`idcliente`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mydb`.`func`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`func` (
  `idfunc` INT NOT NULL AUTO_INCREMENT,
  `nome` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`idfunc`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mydb`.`trans`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`trans` (
  `idtrans` INT NOT NULL AUTO_INCREMENT,
  `idconta` INT NOT NULL,
  `tipo` VARCHAR(45) NOT NULL,
  `quantidade` FLOAT NOT NULL,
  `idfunc` INT NOT NULL,
  `func_idfunc` INT NOT NULL,
  `conta_idconta` INT NOT NULL,
  PRIMARY KEY (`idtrans`, `func_idfunc`, `conta_idconta`),
  INDEX `fk_trans_func1_idx` (`func_idfunc` ASC) VISIBLE,
  INDEX `fk_trans_conta1_idx` (`conta_idconta` ASC) VISIBLE,
  CONSTRAINT `fk_trans_conta1`
    FOREIGN KEY (`conta_idconta`)
    REFERENCES `mydb`.`conta` (`idconta`),
  CONSTRAINT `fk_trans_func1`
    FOREIGN KEY (`func_idfunc`)
    REFERENCES `mydb`.`func` (`idfunc`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `mydb`.`transf`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`transf` (
  `idtransf` INT NOT NULL AUTO_INCREMENT,
  `quantidade` FLOAT NOT NULL,
  `func_idfunc` INT NOT NULL,
  `conta_idconta` INT NOT NULL,
  `conta_idconta1` INT NOT NULL,
  PRIMARY KEY (`idtransf`, `func_idfunc`, `conta_idconta`, `conta_idconta1`),
  INDEX `fk_transf_func1_idx` (`func_idfunc` ASC) VISIBLE,
  INDEX `fk_transf_conta1_idx` (`conta_idconta` ASC) VISIBLE,
  INDEX `fk_transf_conta2_idx` (`conta_idconta1` ASC) VISIBLE,
  CONSTRAINT `fk_transf_conta1`
    FOREIGN KEY (`conta_idconta`)
    REFERENCES `mydb`.`conta` (`idconta`),
  CONSTRAINT `fk_transf_conta2`
    FOREIGN KEY (`conta_idconta1`)
    REFERENCES `mydb`.`conta` (`idconta`),
  CONSTRAINT `fk_transf_func1`
    FOREIGN KEY (`func_idfunc`)
    REFERENCES `mydb`.`func` (`idfunc`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
