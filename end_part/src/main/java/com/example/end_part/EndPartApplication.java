package com.example.end_part;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.transaction.annotation.EnableTransactionManagement;

@SpringBootApplication
@MapperScan(basePackages = "com.example.end_part.mapper")
@EnableTransactionManagement
public class EndPartApplication {

	public static void main(String[] args) {
		SpringApplication.run(EndPartApplication.class, args);
	}

}
