# class Singleton:
#     __instance = None

#     def __new__(cls):
#         if cls.__instance is None:
#             cls.__instance = super().__new__(cls)
#         return cls.__instance


# s1 = Singleton()
# s2 = Singleton()

# print(s1 is s2)  # Output: True


p = PingSensor(16)

while True:
    print(p.get_distance())
    time.sleep(0.5)
