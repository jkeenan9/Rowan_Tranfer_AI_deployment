import streamlit as st
#st.write("Secrets keys:", list(st.secrets.keys())) #Development check to ensure secrets are set on streamlit
from openai import OpenAI
from app.development import schedule_model
from app.development import iResponse
import hmac

shown_warning = False

def password_gate():
    # Session flag (per browser session)
    if "authed" not in st.session_state:
        st.session_state.authed = False

    # If already authenticated, continue
    if st.session_state.authed:
        return

    # Otherwise show login UI and stop the app
    st.title("Rowan ME Transfer Advisor 🔒")
    st.write("Enter the site password to continue. Press login button, **DO NOT** just press the enter key")

    pw = st.text_input("Password", type="password") #Password stored here

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Log in", use_container_width=True):
            if "SITE_PASSWORD" not in st.secrets:
                st.error("Server misconfigured: SITE_PASSWORD secret not set.")
                st.stop()

            if hmac.compare_digest(pw, st.secrets["SITE_PASSWORD"]): #Checks password against streamlit secret password
                st.session_state.authed = True 
                st.rerun()
            else:
                st.error("Incorrect password.")

    with col2:
        if st.button("Clear", use_container_width=True):
            st.session_state.authed = False
            st.rerun()

    st.stop()  # blocks rest of app until authed


st.set_page_config(
    page_title="Rowan ME Transfer Advisor", 
    page_icon="🎓",
    menu_items={ #Does not do anything yet
         'Get Help': 'https://www.extremelycoolapp.com/help',
         'Report a bug': "https://www.extremelycoolapp.com/bug",
         'About': "# This is a header. This is an *extremely* cool app!"
        },
    )

password_gate()

# --- 1) One-time popup on first load (per session) ---
#if shown_warning == False:
if "show_welcome_modal" not in st.session_state:
    st.session_state.show_welcome_modal = True  # first time in this session

@st.dialog("Welcome to Rowan ME Transfer Advisor 🎓")
def welcome_modal():
    st.write(
        "This tool can help you with any transfer questions related to Rowan's mechanical engineering department,\n\n"
        "To build potential schedules, click View tips to see how to ask for a schedule\n\n"
        "**PLEASE UNDERSTAND!!**\n"
        "- Double-check information with official advising resources before making important decisions.\n"
        "- AI can make mistakes.\n"
        "- Don’t paste sensitive info.\n"
        "- This tool is good for general transfer questions, unique or detailed questions could yield inaccurate responses.\n"
    )

    dont_show = st.checkbox("Don’t show this again (this session)", value=False)

    if st.button("View tips"):
        st.info("To build a schedule say: “Make a schedule. I’ve taken Calculus II, Matls Sci. & Manuf., Intro Elect & Magnet")
        st.info("This format must be followed exactly, course names must match the ME flowchart course names exactly. (Use I's for things like Calculus I).")
        st.info("1st year clinics must be typed as: 'First Year Clinic I or First Year Clinic II'.")


    # If they check “don’t show”, respect it immediately
    if dont_show:
        st.session_state.show_welcome_modal = False


#Triggers pop-up window
if st.session_state.show_welcome_modal:
    welcome_modal()

st.title("Rowan ME AI Transfer Advisor 🎓")
st.write(
    "Ask questions about transfering into Rowan's mechanical engineering, or "
    "build a schedule by asking:\n\n"
    "_“Make a schedule. I’ve taken course1, course2, ...”_"
)

# Initialize chat history in session_state
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": "Hi! Ask me any questions you have about transfering into Rowan's ME program, or ask a question about your schedule."
        }
    ]

# Display the chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Remember AI can and will make mistakes.")

if user_input:
    # 1. Add user message to history
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # 2. Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # 3. Decide: schedule mode vs general chat
    # How script decides to operate (general question response vs schedule building response)
    use_schedule_tool = any(
        word in user_input.lower() for word in ["schedule", "make a schedule"] #A good future works is to create a better system for this
    )

    if use_schedule_tool:
        # Build a minimal message list for schedule_model
        # You can pass just the conversation, or only the last user message.
        # Here we pass full history so the system prompt still applies.
        messages_for_tool = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state["messages"]
        ]

        with st.chat_message("assistant"):
            with st.spinner("Building your schedule..."): #Lets the user know system is building schedule
                try:
                    schedule_text = schedule_model(messages_for_tool)
                except Exception as e:
                    schedule_text = f"Sorry, something went wrong while building the schedule: `{e}`"

                st.markdown(schedule_text)

        # Save assistant reply
        st.session_state["messages"].append(
            {"role": "assistant", "content": schedule_text}
        )
    else:
        # General chat using a plain model (no tools)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    general_messages_for_tool = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state["messages"]
                    ]

                    general_response = iResponse(general_messages_for_tool)

                    assistant_content = general_response #This line can probably be removed and general_response can be replaced by assistant_content
                except Exception as e:
                    assistant_content = f"Error talking to the model: `{e}`"

                st.markdown(assistant_content)

                #print(assistant_content) #DEV TESTING -----------------------

        st.session_state["messages"].append(
            {"role": "assistant", "content": assistant_content}
        )

with st.sidebar:
    st.header("📘 Help")
    st.button("How this works", on_click=lambda: st.session_state.update({"show_welcome_modal": True}))
    st.link_button(
        "ME flowchart", 
        "https://engineering.rowan.edu/_docs/mechanical/me-flowchart-nov-2022.pdf"
    )
