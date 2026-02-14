-- =============================================================================
-- Database Views for TSBot
-- =============================================================================

-- View tra cuu diem chuan - JOIN san cac bang de SQL Agent su dung
CREATE OR REPLACE VIEW view_tra_cuu_diem AS
SELECT
    dc.id AS diem_chuan_id,
    t.ma_truong,
    t.ten_truong,
    t.ten_khong_dau,
    t.loai_truong,
    n.ma_nganh,
    n.ten_nganh,
    n.ten_khong_dau AS ten_nganh_khong_dau,
    kt.ma_khoi,
    kt.ten_khoi,
    kt.mon_hoc,
    dc.nam,
    dc.diem_chuan,
    dc.chi_tieu,
    dc.gioi_tinh,
    dc.khu_vuc,
    dc.doi_tuong,
    dc.ghi_chu
FROM diem_chuan dc
JOIN nganh n ON dc.nganh_id = n.id
JOIN truong t ON n.truong_id = t.id
JOIN khoi_thi kt ON dc.khoi_thi_id = kt.id;
