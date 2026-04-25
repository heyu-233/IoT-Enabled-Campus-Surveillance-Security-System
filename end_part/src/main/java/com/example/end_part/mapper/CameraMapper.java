package com.example.end_part.mapper;

import com.example.end_part.entity.Camera;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface CameraMapper {
    @Select("""
            SELECT id,
                   name,
                   device_id AS deviceId,
                   ip_address AS ipAddress,
                   port,
                   location,
                   status,
                   stream_url AS streamUrl,
                   last_active AS lastActive,
                   created_at AS createdAt,
                   updated_at AS updatedAt
            FROM cameras
            ORDER BY created_at DESC
            """)
    List<Camera> findAll();

    @Select("""
            SELECT id,
                   name,
                   device_id AS deviceId,
                   ip_address AS ipAddress,
                   port,
                   location,
                   status,
                   stream_url AS streamUrl,
                   last_active AS lastActive,
                   created_at AS createdAt,
                   updated_at AS updatedAt
            FROM cameras
            WHERE id = #{id}
            """)
    Camera findById(Long id);

    @Insert("""
            INSERT INTO cameras (name, device_id, ip_address, port, location, status, stream_url, last_active, created_at, updated_at)
            VALUES (#{name}, #{deviceId}, #{ipAddress}, #{port}, #{location}, #{status}, #{streamUrl}, #{lastActive}, #{createdAt}, #{updatedAt})
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    void insert(Camera camera);

    @Update("""
            UPDATE cameras
            SET name = #{name},
                device_id = #{deviceId},
                ip_address = #{ipAddress},
                port = #{port},
                location = #{location},
                status = #{status},
                stream_url = #{streamUrl},
                last_active = #{lastActive},
                updated_at = #{updatedAt}
            WHERE id = #{id}
            """)
    void update(Camera camera);

    @Delete("DELETE FROM cameras WHERE id = #{id}")
    void delete(Long id);

    @Update("UPDATE cameras SET status = #{status}, last_active = #{lastActive}, updated_at = #{updatedAt} WHERE id = #{id}")
    void updateStatus(Camera camera);

    @Select("""
            SELECT id,
                   name,
                   device_id AS deviceId,
                   ip_address AS ipAddress,
                   port,
                   location,
                   status,
                   stream_url AS streamUrl,
                   last_active AS lastActive,
                   created_at AS createdAt,
                   updated_at AS updatedAt
            FROM cameras
            WHERE device_id = #{deviceId}
            LIMIT 1
            """)
    Camera findByDeviceId(String deviceId);
}
