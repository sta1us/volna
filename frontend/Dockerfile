# /home/ram/projects/volna/frontend/Dockerfile
FROM node:20-slim

WORKDIR /app/frontend

# Копируем файлы зависимостей фронтенда
COPY package*.json ./
# Если у вас там реально есть requirements.txt для фронта, раскомментируйте:
# RUN apt-get update && apt-get install -y python3 pip && pip install -r requirements.txt

RUN npm install

COPY . .

CMD ["npm", "run", "dev", "--", "--host"]
