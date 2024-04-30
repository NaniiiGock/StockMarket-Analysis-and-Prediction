--
-- PostgreSQL database dump
--

-- Dumped from database version 16.2
-- Dumped by pg_dump version 16.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: login_table; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.login_table (
    id integer NOT NULL,
    username character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    pass_hash character varying(255) NOT NULL
);


ALTER TABLE public.login_table OWNER TO "user";

--
-- Name: login_table_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.login_table_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.login_table_id_seq OWNER TO "user";

--
-- Name: login_table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.login_table_id_seq OWNED BY public.login_table.id;


--
-- Name: user_history; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.user_history (
    transaction_id integer NOT NULL,
    user_id integer NOT NULL,
    sold_or_bought character varying(50) NOT NULL
);


ALTER TABLE public.user_history OWNER TO "user";

--
-- Name: user_history_transaction_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.user_history_transaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_history_transaction_id_seq OWNER TO "user";

--
-- Name: user_history_transaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.user_history_transaction_id_seq OWNED BY public.user_history.transaction_id;


--
-- Name: user_subscriptions; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.user_subscriptions (
    user_id integer NOT NULL,
    stock_id integer NOT NULL
);


ALTER TABLE public.user_subscriptions OWNER TO "user";

--
-- Name: login_table id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.login_table ALTER COLUMN id SET DEFAULT nextval('public.login_table_id_seq'::regclass);


--
-- Name: user_history transaction_id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.user_history ALTER COLUMN transaction_id SET DEFAULT nextval('public.user_history_transaction_id_seq'::regclass);


--
-- Name: login_table login_table_email_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.login_table
    ADD CONSTRAINT login_table_email_key UNIQUE (email);


--
-- Name: login_table login_table_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.login_table
    ADD CONSTRAINT login_table_pkey PRIMARY KEY (id);


--
-- Name: login_table login_table_username_key; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.login_table
    ADD CONSTRAINT login_table_username_key UNIQUE (username);


--
-- Name: user_history user_history_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.user_history
    ADD CONSTRAINT user_history_pkey PRIMARY KEY (transaction_id);


--
-- Name: user_history user_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.user_history
    ADD CONSTRAINT user_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.login_table(id);


--
-- Name: user_subscriptions user_subscriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.user_subscriptions
    ADD CONSTRAINT user_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.login_table(id);


--
-- PostgreSQL database dump complete
--

