from field_generator.field_generator import FieldGenerator

f = FieldGenerator(5, 4)
# for i in range(4):
#     for j in range(5):
#         print(f.field[i][j].x, f.field[i][j].y)
f.print()

print(f.field[0][3].neighbours)
