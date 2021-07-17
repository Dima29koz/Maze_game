from field_generator.field_generator import FieldGenerator


class Field:
    def __init__(self):
        self.field = FieldGenerator(5, 4).get_field()

    def get_field(self):
        return self.field
