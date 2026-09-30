from sonolus_converters import mmws, sus, usc, LevelData, holodori_sus

with open("chart_m0303_expert.sus", "r") as f:
    score = holodori_sus.load(f)

overlaps_score, overlap_count = score.export_overlaps_score()
print(overlap_count)
if overlap_count != 0:
    sus.export("output.sus", overlaps_score)
else:
    sus.export("output.sus", score)