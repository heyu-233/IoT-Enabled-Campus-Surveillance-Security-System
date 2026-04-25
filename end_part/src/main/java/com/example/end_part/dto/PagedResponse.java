package com.example.end_part.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class PagedResponse<T> {
    private List<T> items;
    private long total;
    private int page;
    private int pageSize;
}
