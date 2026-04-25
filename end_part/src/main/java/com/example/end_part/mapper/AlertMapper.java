package com.example.end_part.mapper;

import com.example.end_part.entity.Alert;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;
import java.util.Map;

@Mapper
public interface AlertMapper {
    @Select("""
            <script>
            SELECT a.id,
                   a.behavior_id AS behaviorId,
                   a.type,
                   a.severity,
                   a.status,
                   a.description,
                   a.processed_by AS processedBy,
                   a.processing_notes AS processingNotes,
                   a.processed_at AS processedAt,
                   a.created_at AS createdAt,
                   b.image_url AS screenshot,
                   b.image_url AS processedImageUrl,
                   b.original_image_url AS originalImageUrl,
                   b.confidence AS confidence,
                   b.occurred_at AS behaviorOccurredAt,
                   c.id AS cameraId,
                   c.name AS cameraName,
                   c.location AS cameraLocation
            FROM alerts a
            LEFT JOIN behaviors b ON a.behavior_id = b.id
            LEFT JOIN cameras c ON b.camera_id = c.id
            ORDER BY a.created_at DESC
            LIMIT #{limit} OFFSET #{offset}
            </script>
            """)
    List<Alert> findPage(@Param("limit") int limit, @Param("offset") int offset);

    @Select("SELECT COUNT(*) FROM alerts")
    long countAll();

    @Select("""
            SELECT a.id,
                   a.behavior_id AS behaviorId,
                   a.type,
                   a.severity,
                   a.status,
                   a.description,
                   a.processed_by AS processedBy,
                   a.processing_notes AS processingNotes,
                   a.processed_at AS processedAt,
                   a.created_at AS createdAt,
                   b.image_url AS screenshot,
                   b.image_url AS processedImageUrl,
                   b.original_image_url AS originalImageUrl,
                   b.confidence AS confidence,
                   b.occurred_at AS behaviorOccurredAt,
                   c.id AS cameraId,
                   c.name AS cameraName,
                   c.location AS cameraLocation
            FROM alerts a
            LEFT JOIN behaviors b ON a.behavior_id = b.id
            LEFT JOIN cameras c ON b.camera_id = c.id
            WHERE a.id = #{id}
            """)
    Alert findById(Long id);

    @Insert("INSERT INTO alerts (behavior_id, type, severity, status, description, created_at) VALUES (#{behaviorId}, #{type}, #{severity}, #{status}, #{description}, #{createdAt})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    void insert(Alert alert);

    @Update("UPDATE alerts SET status = #{status}, processed_by = #{processedBy}, processing_notes = #{processingNotes}, processed_at = #{processedAt} WHERE id = #{id}")
    void updateStatus(Alert alert);

    @Delete("DELETE FROM alerts WHERE id = #{id}")
    void delete(Long id);

    @Select("""
            <script>
            SELECT a.id,
                   a.behavior_id AS behaviorId,
                   a.type,
                   a.severity,
                   a.status,
                   a.description,
                   a.processed_by AS processedBy,
                   a.processing_notes AS processingNotes,
                   a.processed_at AS processedAt,
                   a.created_at AS createdAt,
                   b.image_url AS screenshot,
                   b.image_url AS processedImageUrl,
                   b.original_image_url AS originalImageUrl,
                   b.confidence AS confidence,
                   b.occurred_at AS behaviorOccurredAt,
                   c.id AS cameraId,
                   c.name AS cameraName,
                   c.location AS cameraLocation
            FROM alerts a
            LEFT JOIN behaviors b ON a.behavior_id = b.id
            LEFT JOIN cameras c ON b.camera_id = c.id
            <where>
                <if test="keyword != null and keyword != ''">
                    (
                        LOWER(a.type) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                        OR LOWER(a.description) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                        OR LOWER(a.status) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                        OR LOWER(a.severity) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                    )
                </if>
                <if test="status != null and status != ''">
                    AND a.status = #{status}
                </if>
                <if test="from != null and from != ''">
                    AND a.created_at &gt;= #{from}
                </if>
                <if test="to != null and to != ''">
                    AND a.created_at &lt;= #{to}
                </if>
            </where>
            ORDER BY a.created_at DESC
            LIMIT #{limit} OFFSET #{offset}
            </script>
            """)
    List<Alert> search(Map<String, Object> params);

    @Select("""
            <script>
            SELECT COUNT(*)
            FROM alerts a
            <where>
                <if test="keyword != null and keyword != ''">
                    (
                        LOWER(a.type) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                        OR LOWER(a.description) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                        OR LOWER(a.status) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                        OR LOWER(a.severity) LIKE CONCAT('%', LOWER(#{keyword}), '%')
                    )
                </if>
                <if test="status != null and status != ''">
                    AND a.status = #{status}
                </if>
                <if test="from != null and from != ''">
                    AND a.created_at &gt;= #{from}
                </if>
                <if test="to != null and to != ''">
                    AND a.created_at &lt;= #{to}
                </if>
            </where>
            </script>
            """)
    long searchCount(Map<String, Object> params);

    @Select("""
            SELECT DATE_FORMAT(created_at, '%Y-%m-%d') AS label, COUNT(*) AS value
            FROM alerts
            GROUP BY DATE_FORMAT(created_at, '%Y-%m-%d')
            ORDER BY label ASC
            """)
    List<Map<String, Object>> countDaily();

    @Select("SELECT COUNT(*) FROM alerts WHERE type = #{type}")
    long countByType(String type);

    @Select("SELECT COUNT(*) FROM alerts WHERE type = #{type} AND status = 'PROCESSED'")
    long countProcessedByType(String type);

    @Select("""
            SELECT type AS name, COUNT(*) AS value
            FROM alerts
            GROUP BY type
            ORDER BY value DESC, type ASC
            """)
    List<Map<String, Object>> countDistribution();

    @Select("""
            SELECT COALESCE(c.location, 'Unknown') AS name, COUNT(*) AS value
            FROM alerts a
            LEFT JOIN behaviors b ON a.behavior_id = b.id
            LEFT JOIN cameras c ON b.camera_id = c.id
            GROUP BY COALESCE(c.location, 'Unknown')
            ORDER BY value DESC, name ASC
            """)
    List<Map<String, Object>> countByArea();

    @Select("""
            SELECT DATE_FORMAT(a.created_at, '%Y-%m-%d') AS label, COUNT(*) AS value
            FROM alerts a
            WHERE a.type = #{type}
            GROUP BY DATE_FORMAT(a.created_at, '%Y-%m-%d')
            ORDER BY label ASC
            """)
    List<Map<String, Object>> countTimelineByType(String type);
}
