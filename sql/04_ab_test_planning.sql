-- Experiment planning only; no outcomes.
SELECT registration_date,COUNT(*) source4_new_users FROM user_growth_profile
WHERE registered_via=4 AND registration_date BETWEEN '2015-10-07' AND '2015-10-16'
GROUP BY registration_date ORDER BY registration_date;
SELECT COUNT(*) d7_eligible_users,SUM(d7_retained) d7_retained_users,
AVG(d7_retained) baseline_d7_retention FROM user_growth_profile
WHERE registered_via=4 AND registration_date BETWEEN '2015-10-07' AND '2015-10-09'
AND d7_eligible_flag=1;
-- alpha=5%, power=80%, MDE=0.3pp, 50/50 allocation.
WITH d AS(SELECT AVG(d7_retained) p1,0.003 mde,1.959964 za,0.841621 zp
FROM user_growth_profile WHERE registered_via=4
AND registration_date BETWEEN '2015-10-07' AND '2015-10-09' AND d7_eligible_flag=1),
p AS(SELECT p1,p1+mde p2,(2*p1+mde)/2 pb,mde,za,zp FROM d),
n AS(SELECT CEILING(POWER(za*SQRT(2*pb*(1-pb))+
zp*SQRT(p1*(1-p1)+p2*(1-p2)),2)/POWER(mde,2)) per_group FROM p)
SELECT per_group,2*per_group total_required FROM n;
-- Read D7 seven days after final enrollment.
-- D30 is future long-term validation only, not current evidence.
