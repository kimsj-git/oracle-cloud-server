FROM node:18.16.0 as builder

RUN mkdir /usr/src/app

WORKDIR /usr/src/app

ENV PATH /usr/src/app/node_modules/.bin:$PATH

COPY package.json /usr/src/app/package.json

RUN npm install -g npm@9.6.5
RUN npm install 
RUN npm install react-scripts@3.4.1 -g

COPY . /usr/src/app

RUN npm run build

FROM nginx

RUN rm -rf /etc/nginx/conf.d

COPY conf /etc/nginx

COPY --from=builder /usr/src/app/build /usr/share/nginx/html

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
