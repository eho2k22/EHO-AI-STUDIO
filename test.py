import base64

# Encode string to unique number
def encode_string(string):
    encoded_bytes = base64.b64encode(string.encode())
    return int.from_bytes(encoded_bytes, 'big')

# Decode unique number to string
def decode_number(number):
    decoded_bytes = number.to_bytes((number.bit_length() + 7) // 8, 'big')
    return base64.b64decode(decoded_bytes).decode()

# Example usage
string = input("Enter a String: ")
encoded = encode_string(string)
print("Encoded Number is: ")
print(encoded)
decoded = decode_number(encoded)
print("Decoded String is:")
print(decoded)




usertext = input("Enter your VIP Secret Number: ")
try:
    usernumber = int(usertext)
    print("The UserText converted to an integer: ", usernumber)
except ValueError:
    print("The UserText entered is not a number.")

secretkey = decode_number(usernumber)
print("Number is : ")
print(usernumber)
print("Decoded Secret Key is :")
print(secretkey)



