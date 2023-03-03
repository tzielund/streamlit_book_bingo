import streamlit_authenticator

hashed = streamlit_authenticator.Hasher(['saving the galaxy']).generate()
print (hashed)
