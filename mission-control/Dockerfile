# Use the official Node.js Alpine image (Alpine is a super tiny Linux distro)
FROM node:22-alpine
# Set the working directory inside the container
WORKDIR /app

# Copy package.json files first to leverage Docker caching
COPY package.json package-lock.json* ./

# Install node modules
RUN npm install

# Copy the rest of the React code into the container
COPY . .

# Expose the port Vite runs on
EXPOSE 5173

# Command to start the Vite dev server
# The --host 0.0.0.0 flag is CRITICAL. Without it, Vite only serves to localhost
# inside the container, and your Windows browser won't be able to see it!
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
