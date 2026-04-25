package com.example.end_part.mapper;

import com.example.end_part.entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Update;

@Mapper
public interface UserMapper {
    @Select("SELECT * FROM users WHERE username = #{username}")
    User findByUsername(String username);

    @Insert("INSERT INTO users (username, password, email, role, created_at, updated_at) VALUES (#{username}, #{password}, #{email}, #{role}, #{createdAt}, #{updatedAt})")
    void insert(User user);

    @Select("SELECT * FROM users WHERE id = #{id}")
    User findById(Long id);

    @Update("UPDATE users SET password = #{password}, email = #{email}, role = #{role}, updated_at = #{updatedAt} WHERE id = #{id}")
    void update(User user);
}
