package com.example.end_part.mapper;

import com.example.end_part.entity.Behavior;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;

import java.util.List;
import java.util.Map;

@Mapper
public interface BehaviorMapper {
    @Select("""
            SELECT id,
                   camera_id AS cameraId,
                   type,
                   description,
                   image_url AS imageUrl,
                   image_url AS processedImageUrl,
                   original_image_url AS originalImageUrl,
                   confidence,
                   occurred_at AS occurredAt,
                   created_at AS createdAt
            FROM behaviors
            ORDER BY occurred_at DESC, created_at DESC
            """)
    List<Behavior> findAll();

    @Select("""
            SELECT id,
                   camera_id AS cameraId,
                   type,
                   description,
                   image_url AS imageUrl,
                   image_url AS processedImageUrl,
                   original_image_url AS originalImageUrl,
                   confidence,
                   occurred_at AS occurredAt,
                   created_at AS createdAt
            FROM behaviors
            WHERE id = #{id}
            """)
    Behavior findById(Long id);

    @Insert("""
            INSERT INTO behaviors (
                camera_id,
                type,
                description,
                image_url,
                original_image_url,
                confidence,
                occurred_at,
                created_at
            ) VALUES (
                #{cameraId},
                #{type},
                #{description},
                #{imageUrl},
                #{originalImageUrl},
                #{confidence},
                #{occurredAt},
                #{createdAt}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    void insert(Behavior behavior);

    @Delete("DELETE FROM behaviors WHERE id = #{id}")
    void delete(Long id);

    @Select("""
            SELECT type AS name, COUNT(*) AS value
            FROM behaviors
            GROUP BY type
            ORDER BY value DESC, type ASC
            """)
    List<Map<String, Object>> countByType();

    @Select("""
            SELECT COALESCE(c.location, 'Unknown') AS name, COUNT(*) AS value
            FROM behaviors b
            LEFT JOIN cameras c ON b.camera_id = c.id
            GROUP BY COALESCE(c.location, 'Unknown')
            ORDER BY value DESC, name ASC
            """)
    List<Map<String, Object>> countByArea();

    @Select("""
            SELECT DATE_FORMAT(occurred_at, '%Y-%m-%d') AS label, COUNT(*) AS value
            FROM behaviors
            WHERE type = #{type}
            GROUP BY DATE_FORMAT(occurred_at, '%Y-%m-%d')
            ORDER BY label ASC
            """)
    List<Map<String, Object>> countByTypeTimeline(String type);

    @Select("""
            SELECT AVG(confidence)
            FROM behaviors
            WHERE type = #{type}
            """)
    Double averageConfidenceByType(String type);
}
