package com.edu.agent.common.base;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * Base entity with common audit fields for all database tables.
 */
@Data
public class BaseEntity implements Serializable {

    private static final long serialVersionUID = 1L;

    /** Primary key, auto-increment */
    @TableId(type = IdType.AUTO)
    private Long id;

    /** Record creation time, auto-filled on insert */
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    /** Record last update time, auto-filled on insert and update */
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    /** Logical delete flag: 0 = not deleted, 1 = deleted */
    @TableLogic
    private Integer deleted;
}
