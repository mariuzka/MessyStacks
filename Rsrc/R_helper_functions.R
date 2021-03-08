library(ggplot2)

calculate_max_dev <- function(r, n, m){
  fl <- (n*r)/m  # lines filled up with carts
  cfl <- floor(fl) # completely filled lines
  max_deviation <- cfl*(m-n) + max(0, ((fl - cfl - n/m) * m))
  return(max_deviation)
}

calculate_prop_max_dev <- function(r, p, m){
  n <- round(p * m)
  max_dev <- calculate_max_dev(r, n, m)
  prop_max_dev <- max_dev / (r*m)
  return(prop_max_dev)
}

messy_parabell <- function(s, n, m){
  -(s/m)*(n-m/2)**2 + s*m/4
}

prop_max_mess <- function(s, p){
  return((floor(s*p)*(1-p) + max(0, ((s*p - floor(s*p) - p))))/s)
}

create_max_mess_df <- function(
  elements_per_stack_range,
  elements_per_stack_inc,
  stacks_range,
  stacks_inc,
  max_elements_per_stack
){
  stacks <- seq(stacks_range[1], stacks_range[2], stacks_inc)
  elements_per_stack <- seq(elements_per_stack_range[1], elements_per_stack_range[2], elements_per_stack_inc)
  
  df <- data.frame(matrix(ncol=5, nrow=length(elements_per_stack)*length(stacks)))
  names(df) <- c(
    "stacks", 
    "elements_per_stack", 
    "max_elements_per_stack", 
    "max_deviation",
    "max_parabola_deviation"
  )
  
  df$stacks <- stacks
  df$stacks <- sort(df$stacks)
  df$elements_per_stack <- elements_per_stack
  df$max_elements_per_stack <- max_elements_per_stack
  
  df$prop_elements_per_stack <- df$elements_per_stack / df$max_elements_per_stack
  
  for (i in 1:nrow(df)){
    
    df[i, "max_deviation"] <- calculate_max_dev(
      df[i, "stacks"], 
      df[i, "elements_per_stack"], 
      df[i, "max_elements_per_stack"]
    )
    
    df[i, "max_parabola_deviation"] <- messy_parabell(
      df[i, "stacks"], 
      df[i, "elements_per_stack"], 
      df[i, "max_elements_per_stack"]
    )
    
    
  }
  
  df$elements_total <- df$stacks * df$elements_per_stack
  df$ratio1 <- df$max_deviation/df$elements_total
  df$ratio2 <- df$elements_total/df$max_deviation
  df$prop_max_deviation <- df$max_deviation/ (df$max_elements_per_stack * df$stacks)
  df$prop_max_parabola_deviation <- df$max_parabola_deviation / (df$max_elements_per_stack * df$stacks)
  
  return(df)
}

plot1 <- function(df){
  ggplot(
    data = df, 
    mapping = aes(
      x = elements_per_stack, 
      y = max_deviation, 
      group = as.factor(stacks), 
      color = as.factor(stacks)
    )
  )+
    geom_line(lwd = 1)
}

plot2 <- function(df){
  ggplot(
    data = df, 
    mapping = aes(
      x = elements_total,
      y = max_deviation, 
      group = stacks, 
      color = as.factor(stacks)
    )
  )+
    geom_line(lwd = 1)
}

plot4 <- function(df){
  ggplot(
    data = df, #[df$elements_per_stack %in% seq(1,100,3), ], 
    mapping = aes(
      x = elements_per_stack,
      y = ratio1, 
      color = as.factor(stacks),
      group = as.factor(stacks)
    )
  )+
    geom_line()
}

plot5 <- function(df){
  ggplot(
    data = df, 
    mapping = aes(
      x = prop_elements_per_stack, 
      y = prop_max_deviation, 
      group = as.factor(stacks), 
      color = as.factor(stacks)
    )
  )+
    geom_line(lwd = 1)
}
